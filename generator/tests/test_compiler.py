from datetime import date
from pathlib import Path

from pulse_generator.compiler import compile_music_spec
from pulse_generator.domain import CommunityPulseSnapshot


def test_spec_is_reproducible_and_calming() -> None:
    fixture = Path("fixtures/illustrative-pnw.json").read_text()
    snapshot = CommunityPulseSnapshot.model_validate_json(fixture)
    day = date(2026, 11, 2)
    first = compile_music_spec(snapshot, day)
    second = compile_music_spec(snapshot, day)

    assert first.seed == second.seed
    assert first.tempo_bpm == second.tempo_bpm
    assert 64 <= first.tempo_bpm <= 80
    assert first.snapshot_status == "illustrative"
    assert "vocals" in first.negative_prompt
