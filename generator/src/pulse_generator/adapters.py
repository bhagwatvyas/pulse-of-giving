"""Contracts for self-hosted music-model integrations.

Production adapters belong behind this boundary.  The fixture adapter is deliberately
non-production: it creates deterministic WAV files so that the artifact pipeline can
be exercised without model weights, a GPU, or an external generation API.
"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path
from typing import Protocol

from .domain import GeneratedCandidate, ModelProvenance, MusicSpec


class MusicModelAdapter(Protocol):
    """A pinned, self-hosted music model capable of producing candidates."""

    provenance: ModelProvenance

    def generate(
        self,
        spec: MusicSpec,
        *,
        candidate_count: int,
        output_directory: Path,
    ) -> list[GeneratedCandidate]:
        """Write generated audio below output_directory and return its provenance."""


class FixtureToneAdapter:
    """Test-only adapter that emits calm reference tones, never model inference."""

    provenance = ModelProvenance(
        model_id="pulse-of-giving-fixture-tone",
        revision="fixture-v1",
        upstream_license="Internal test fixture; not a generative model",
        reviewed_at="2026-11-02",
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
        candidates: list[GeneratedCandidate] = []
        for index in range(candidate_count):
            candidate_id = f"fixture-{index:03d}"
            audio_path = output_directory / f"{candidate_id}.wav"
            self._write_tone(
                audio_path,
                duration_seconds=spec.duration_seconds,
                frequency_hz=220 + (index * 17),
            )
            candidates.append(
                GeneratedCandidate(
                    candidate_id=candidate_id,
                    audio_path=audio_path,
                    effective_parameters={
                        "adapter": "fixture-tone",
                        "candidate_index": index,
                        "seed": spec.seed + index,
                        "sample_rate_hz": 8_000,
                    },
                )
            )
        return candidates

    @staticmethod
    def _write_tone(path: Path, *, duration_seconds: int, frequency_hz: int) -> None:
        sample_rate_hz = 8_000
        sample_count = sample_rate_hz * duration_seconds
        with wave.open(str(path), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(sample_rate_hz)
            for frame in range(sample_count):
                # Keep the fixture intentionally quiet and fade both ends.
                position = frame / sample_rate_hz
                fade = min(1.0, position / 0.75, (duration_seconds - position) / 0.75)
                amplitude = int(3_000 * fade * math.sin(2 * math.pi * frequency_hz * position))
                output.writeframesraw(struct.pack("<h", amplitude))
