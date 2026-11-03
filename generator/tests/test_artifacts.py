from datetime import date
from pathlib import Path

import pytest

from pulse_generator.adapters import FixtureToneAdapter
from pulse_generator.analysis import FixtureMetricsAnalyzer
from pulse_generator.artifacts import (
    ArtifactManifest,
    ArtifactStatus,
    approve_artifact,
    build_artifact,
    write_json,
)
from pulse_generator.compiler import compile_music_spec
from pulse_generator.domain import CommunityPulseSnapshot, SnapshotStatus


def fixture_snapshot() -> CommunityPulseSnapshot:
    return CommunityPulseSnapshot.model_validate_json(
        Path("fixtures/illustrative-pnw.json").read_text()
    )


def build_fixture_run(tmp_path: Path) -> tuple[Path, ArtifactManifest]:
    snapshot = fixture_snapshot()
    adapter = FixtureToneAdapter()
    spec = compile_music_spec(snapshot, date(2026, 11, 2), model_id=adapter.provenance.model_id)
    destination = build_artifact(
        root=tmp_path,
        snapshot=snapshot,
        spec=spec,
        adapter=adapter,
        analyzer=FixtureMetricsAnalyzer(),
        candidate_count=2,
    )
    return destination, ArtifactManifest.model_validate_json((destination / "manifest.json").read_text())


def test_fixture_run_is_immutable_and_selects_only_a_passing_candidate(tmp_path: Path) -> None:
    destination, manifest = build_fixture_run(tmp_path)

    assert manifest.status == ArtifactStatus.PENDING_REVIEW
    assert manifest.selected_candidate_id == "fixture-000"
    assert len(manifest.candidates) == 2
    assert manifest.candidates[0].evaluation.passed
    assert not manifest.candidates[1].evaluation.passed
    assert (destination / manifest.candidates[0].audio_file).is_file()
    assert len(manifest.candidates[0].sha256) == 64
    with pytest.raises(FileExistsError):
        build_artifact(
            root=tmp_path,
            snapshot=fixture_snapshot(),
            spec=manifest.music_spec,
            adapter=FixtureToneAdapter(),
            analyzer=FixtureMetricsAnalyzer(),
            candidate_count=2,
        )


def test_illustrative_run_cannot_be_promoted(tmp_path: Path) -> None:
    _, manifest = build_fixture_run(tmp_path)

    with pytest.raises(ValueError, match="illustrative snapshots"):
        approve_artifact(root=tmp_path, artifact_id=manifest.artifact_id, reviewer="Vyas")
    assert not (tmp_path / "current.json").exists()


def test_model_identity_must_match_the_music_spec(tmp_path: Path) -> None:
    snapshot = fixture_snapshot()
    spec = compile_music_spec(snapshot, date(2026, 11, 2), model_id="a-different-model")

    with pytest.raises(ValueError, match="same model release"):
        build_artifact(
            root=tmp_path,
            snapshot=snapshot,
            spec=spec,
            adapter=FixtureToneAdapter(),
            analyzer=FixtureMetricsAnalyzer(),
            candidate_count=1,
        )


def test_only_a_reviewed_verified_and_release_eligible_run_can_be_promoted(tmp_path: Path) -> None:
    destination, manifest = build_fixture_run(tmp_path)
    eligible = manifest.model_copy(
        update={
            "snapshot_status": SnapshotStatus.VERIFIED,
            "model": manifest.model.model_copy(update={"release_eligible": True}),
        }
    )
    write_json(destination / "manifest.json", eligible.model_dump(mode="json"))

    pointer = approve_artifact(root=tmp_path, artifact_id=eligible.artifact_id, reviewer="Vyas Bhagwat")
    approved = ArtifactManifest.model_validate_json((destination / "manifest.json").read_text())

    assert pointer.artifact_id == eligible.artifact_id
    assert (tmp_path / "current.json").is_file()
    assert approved.status == ArtifactStatus.APPROVED
    assert approved.human_reviewer == "Vyas Bhagwat"
