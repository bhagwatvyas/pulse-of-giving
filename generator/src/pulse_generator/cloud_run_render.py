"""One-off Cloud Run job entry point for a private, review-only model render."""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import time
from datetime import date
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from .ace_step_adapter import AceStepApiAdapter
from .analysis import PendingAnalysis
from .artifacts import build_artifact
from .compiler import compile_music_spec
from .domain import CommunityPulseSnapshot


def wait_for_health(endpoint: str, timeout_seconds: int = 1_200) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urlopen(f"{endpoint.rstrip('/')}/health", timeout=10) as response:  # noqa: S310 - loopback service
                if response.status == 200:
                    return
        except URLError:
            time.sleep(5)
    raise TimeoutError("ACE-Step API did not become healthy before the job deadline")


def upload_directory(*, directory: Path, bucket_name: str, prefix: str) -> str:
    from google.cloud import storage

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    for source in directory.rglob("*"):
        if source.is_file():
            key = "/".join((prefix.strip("/"), directory.name, str(source.relative_to(directory))))
            bucket.blob(key).upload_from_filename(source)
    return f"gs://{bucket_name}/{prefix.strip('/')}/{directory.name}/"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render one private ACE-Step artifact in Cloud Run.")
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--date", type=date.fromisoformat, required=True)
    parser.add_argument("--out", type=Path, default=Path("/tmp/pulse-artifacts"))
    parser.add_argument("--prefix", default="review-only")
    args = parser.parse_args()

    endpoint = "http://127.0.0.1:8001"
    api_environment = os.environ | {
        "ACESTEP_API_HOST": "127.0.0.1",
        "ACESTEP_API_PORT": "8001",
        "ACESTEP_INIT_LLM": "false",
        "ACESTEP_CONFIG_PATH": "acestep-v15-turbo",
        "TOKENIZERS_PARALLELISM": "false",
    }
    api = subprocess.Popen(
        ["/opt/ace-step/.venv/bin/python", "-m", "acestep.api_server", "--host", "127.0.0.1", "--port", "8001"],
        env=api_environment,
    )
    try:
        wait_for_health(endpoint)
        snapshot = CommunityPulseSnapshot.model_validate_json(args.snapshot.read_text())
        adapter = AceStepApiAdapter(
            endpoint=endpoint,
            model_id="acestep-v15-turbo",
            revision=args.revision,
            reviewed_at=args.date.isoformat(),
        )
        spec = compile_music_spec(snapshot, args.date, model_id=adapter.provenance.model_id)
        destination = build_artifact(
            root=args.out,
            snapshot=snapshot,
            spec=spec,
            adapter=adapter,
            analyzer=PendingAnalysis(),
            candidate_count=1,
        )
        uploaded = upload_directory(directory=destination, bucket_name=args.bucket, prefix=args.prefix)
        print(f"PULSE_ARTIFACT_URI={uploaded}", flush=True)
    finally:
        if api.poll() is None:
            api.send_signal(signal.SIGTERM)
            try:
                api.wait(timeout=30)
            except subprocess.TimeoutExpired:
                api.kill()
        shutil.rmtree(args.out, ignore_errors=True)


if __name__ == "__main__":
    main()
