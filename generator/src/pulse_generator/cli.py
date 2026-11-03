import argparse
import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .compiler import compile_music_spec
from .domain import CommunityPulseSnapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile a provenance-aware MusicSpec.")
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=datetime.now(ZoneInfo("America/Los_Angeles")).date(),
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    snapshot = CommunityPulseSnapshot.model_validate_json(args.snapshot.read_text())
    spec = compile_music_spec(snapshot, args.date)
    rendered = json.dumps(spec.model_dump(mode="json"), indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
