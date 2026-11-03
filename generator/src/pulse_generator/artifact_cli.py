"""Local commands for creating a review-only fixture artifact and promoting runs."""

from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .adapters import FixtureToneAdapter
from .analysis import FixtureMetricsAnalyzer
from .artifacts import approve_artifact, build_artifact
from .compiler import compile_music_spec
from .domain import CommunityPulseSnapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a reviewable Pulse of Giving audio artifact.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("fixture", help="Run the test-only adapter; output can never be public.")
    create.add_argument("--snapshot", required=True, type=Path)
    create.add_argument("--out", required=True, type=Path)
    create.add_argument("--candidates", type=int, default=2)
    create.add_argument(
        "--date",
        type=date.fromisoformat,
        default=datetime.now(ZoneInfo("America/Los_Angeles")).date(),
    )

    approve = subparsers.add_parser("approve", help="Promote an eligible, human-reviewed artifact.")
    approve.add_argument("--root", required=True, type=Path)
    approve.add_argument("--artifact-id", required=True)
    approve.add_argument("--reviewer", required=True)

    args = parser.parse_args()
    if args.command == "fixture":
        snapshot = CommunityPulseSnapshot.model_validate_json(args.snapshot.read_text())
        adapter = FixtureToneAdapter()
        spec = compile_music_spec(snapshot, args.date, model_id=adapter.provenance.model_id)
        destination = build_artifact(
            root=args.out,
            snapshot=snapshot,
            spec=spec,
            adapter=adapter,
            analyzer=FixtureMetricsAnalyzer(),
            candidate_count=args.candidates,
        )
        print(destination)
    elif args.command == "approve":
        pointer = approve_artifact(root=args.root, artifact_id=args.artifact_id, reviewer=args.reviewer)
        print(pointer.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
