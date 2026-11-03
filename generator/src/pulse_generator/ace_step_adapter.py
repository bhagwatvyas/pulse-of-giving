"""Adapter for a self-hosted ACE-Step API service.

The worker talks only to a caller-provided endpoint. No prompt or generated audio is
sent to a third-party music API; deployment is responsible for hosting ACE-Step.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .domain import GeneratedCandidate, ModelProvenance, MusicSpec


@dataclass(frozen=True)
class AceStepApiAdapter:
    """Generate deterministic candidate requests against a self-hosted ACE-Step API."""

    endpoint: str
    model_id: str
    revision: str
    reviewed_at: str
    poll_interval_seconds: float = 3.0
    timeout_seconds: int = 1_200

    @property
    def provenance(self) -> ModelProvenance:
        return ModelProvenance(
            model_id=self.model_id,
            revision=self.revision,
            upstream_license="MIT (ACE-Step upstream; release review still required)",
            reviewed_at=self.reviewed_at,
            # A locally rendered test must still pass our own model and audio review.
            release_eligible=False,
        )

    def generate(
        self,
        spec: MusicSpec,
        *,
        candidate_count: int,
        output_directory: Path,
    ) -> list[GeneratedCandidate]:
        if candidate_count < 1:
            raise ValueError("candidate_count must be at least one")
        output_directory.mkdir(parents=True, exist_ok=True)
        generated: list[GeneratedCandidate] = []
        for index in range(candidate_count):
            seed = spec.seed + index
            task_response = self._post_json(
                "/release_task",
                {
                    "prompt": spec.prompt,
                    "lyrics": "[Instrumental]",
                    "thinking": False,
                    "audio_format": "wav",
                    "model": self.model_id,
                    "bpm": spec.tempo_bpm,
                    "audio_duration": spec.duration_seconds,
                    "inference_steps": 8,
                    "shift": 3.0,
                    "use_random_seed": False,
                    "seed": seed,
                },
            )
            task_key = self._task_id(task_response)
            result = self._wait_for_task(task_key)
            remote_path = self._audio_path(result)
            candidate_id = f"ace-step-{index:03d}"
            destination = output_directory / f"{candidate_id}.wav"
            # ACE-Step versions return either a filesystem path or an already
            # signed local API path. Preserve the latter verbatim: encoding it
            # again produces a nested `/v1/audio?path=/v1/audio?...` URL.
            audio_url = (
                remote_path
                if remote_path.startswith("/v1/audio?")
                else "/v1/audio?" + urlencode({"path": remote_path})
            )
            self._download(audio_url, destination)
            generated.append(
                GeneratedCandidate(
                    candidate_id=candidate_id,
                    audio_path=destination,
                    effective_parameters={
                        "adapter": "ace-step-api",
                        "endpoint": self.endpoint,
                        "model": self.model_id,
                        "revision": self.revision,
                        "candidate_index": index,
                        "seed": seed,
                        "prompt": spec.prompt,
                        "negative_prompt": spec.negative_prompt,
                        "instrumental": True,
                        "bpm": spec.tempo_bpm,
                        "duration_seconds": spec.duration_seconds,
                        "inference_steps": 8,
                        "shift": 3.0,
                        "remote_task_id": task_key,
                    },
                )
            )
        return generated

    def _wait_for_task(self, task_id: str) -> dict[str, Any]:
        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            response = self._post_json("/query_result", {"task_id_list": [task_id]})
            result = self._query_result(response, task_id)
            status = result.get("status")
            if status == 1:
                return result
            if status == 2:
                raise RuntimeError(f"ACE-Step task {task_id} failed: {result}")
            time.sleep(self.poll_interval_seconds)
        raise TimeoutError(f"ACE-Step task {task_id} exceeded {self.timeout_seconds} seconds")

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            self._url(path),
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=30) as response:  # noqa: S310 - endpoint is explicit operator input
            decoded = json.loads(response.read().decode("utf-8"))
        if not isinstance(decoded, dict):
            raise RuntimeError(f"ACE-Step returned non-object JSON: {decoded!r}")
        return decoded

    def _download(self, path: str, destination: Path) -> None:
        with urlopen(self._url(path), timeout=120) as response:  # noqa: S310 - endpoint is explicit operator input
            destination.write_bytes(response.read())
        if destination.stat().st_size == 0:
            raise RuntimeError("ACE-Step returned an empty audio file")

    def _url(self, path: str) -> str:
        return self.endpoint.rstrip("/") + path

    @staticmethod
    def _task_id(response: dict[str, Any]) -> str:
        response = AceStepApiAdapter._unwrap(response)
        for key in ("task_id", "taskId", "id"):
            value = response.get(key)
            if isinstance(value, str) and value:
                return value
        raise RuntimeError(f"ACE-Step response did not include a task id: {response}")

    @staticmethod
    def _audio_path(result: dict[str, Any]) -> str:
        result = AceStepApiAdapter._unwrap(result)
        nested_result = result.get("result")
        if isinstance(nested_result, str):
            try:
                parsed = json.loads(nested_result)
            except json.JSONDecodeError:
                parsed = []
            if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                result = parsed[0]
        for key in ("audio_path", "audioPath", "path"):
            value = result.get(key)
            if isinstance(value, str) and value:
                return value
        value = result.get("file")
        if isinstance(value, str) and value:
            return value
        data = result.get("data")
        if isinstance(data, dict):
            for key in ("audio_path", "audioPath", "path"):
                value = data.get(key)
                if isinstance(value, str) and value:
                    return value
        raise RuntimeError(f"ACE-Step result did not include an audio path: {result}")

    @staticmethod
    def _unwrap(response: dict[str, Any]) -> dict[str, Any]:
        """ACE-Step wraps API payloads in ``{data, code, ...}``."""
        data = response.get("data")
        return data if isinstance(data, dict) else response

    @staticmethod
    def _query_result(response: dict[str, Any], task_id: str) -> dict[str, Any]:
        data = response.get("data")
        if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
            raise RuntimeError(f"ACE-Step query returned an unexpected response: {response}")
        item = data[0]
        if item.get("task_id") != task_id:
            raise RuntimeError(f"ACE-Step query returned the wrong task: {item}")
        return item
