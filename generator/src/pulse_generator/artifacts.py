"""Immutable local artifacts and the manual promotion gate for public playback."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .adapters import MusicModelAdapter
from .analysis import CandidateAnalyzer
from .domain import (
    CommunityPulseSnapshot,
    EvaluationResult,
    ModelProvenance,
    MusicSpec,
    SnapshotStatus,
)
from .evaluator import evaluate_candidate


class ArtifactStatus(StrEnum):
    PENDING_REVIEW = "pending_human_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class CandidateArtifact(BaseModel):
    candidate_id: str
    audio_file: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    effective_parameters: dict[str, Any]
    measurement_origin: str
    evaluation: EvaluationResult
    rank_score: float


class ArtifactManifest(BaseModel):
    schema_version: int = 1
    artifact_id: str
    status: ArtifactStatus
    created_at: datetime
    snapshot_id: str
    snapshot_status: SnapshotStatus
    snapshot: CommunityPulseSnapshot
    pacific_date: str
    music_spec: MusicSpec
    model: ModelProvenance
    candidates: list[CandidateArtifact]
    selected_candidate_id: str | None = None
    human_reviewer: str | None = None
    approved_at: datetime | None = None


class CurrentArtifactPointer(BaseModel):
    schema_version: int = 1
    artifact_id: str
    manifest_file: str
    manifest_sha256: str
    snapshot_id: str
    approved_at: datetime


def artifact_directory(root: Path, spec: MusicSpec) -> Path:
    suffix = f"{spec.seed:016x}"[:12]
    return root / spec.pacific_date.isoformat() / f"{spec.snapshot_id}-{suffix}"


def build_artifact(
    *,
    root: Path,
    snapshot: CommunityPulseSnapshot,
    spec: MusicSpec,
    adapter: MusicModelAdapter,
    analyzer: CandidateAnalyzer,
    candidate_count: int,
    created_at: datetime | None = None,
) -> Path:
    """Create a reviewable immutable run. This function never updates current.json."""
    if snapshot.snapshot_id != spec.snapshot_id:
        raise ValueError("snapshot and music spec must have the same snapshot_id")
    if spec.model_id != adapter.provenance.model_id:
        raise ValueError("music spec and adapter must name the same model release")

    destination = artifact_directory(root, spec)
    if destination.exists():
        raise FileExistsError(f"artifact already exists: {destination}")
    candidates_directory = destination / "candidates"
    candidates_directory.mkdir(parents=True)

    generated = adapter.generate(
        spec,
        candidate_count=candidate_count,
        output_directory=candidates_directory,
    )
    if len(generated) != candidate_count:
        raise ValueError("adapter returned a different number of candidates than requested")

    candidate_artifacts: list[CandidateArtifact] = []
    for candidate in generated:
        resolved_audio = candidate.audio_path.resolve()
        if candidates_directory.resolve() not in resolved_audio.parents:
            raise ValueError("adapter emitted audio outside the artifact directory")
        if not resolved_audio.is_file():
            raise FileNotFoundError(f"adapter did not create {resolved_audio}")
        analysis = analyzer.analyze(candidate, spec)
        evaluation = evaluate_candidate(analysis.metrics)
        candidate_artifacts.append(
            CandidateArtifact(
                candidate_id=candidate.candidate_id,
                audio_file=str(resolved_audio.relative_to(destination.resolve())),
                sha256=sha256_file(resolved_audio),
                effective_parameters=candidate.effective_parameters,
                measurement_origin=analysis.measurement_origin,
                evaluation=evaluation,
                rank_score=rank_score(evaluation),
            )
        )

    passing = [candidate for candidate in candidate_artifacts if candidate.evaluation.passed]
    selected = max(passing, key=lambda candidate: candidate.rank_score, default=None)
    manifest = ArtifactManifest(
        artifact_id=destination.name,
        status=ArtifactStatus.PENDING_REVIEW if selected else ArtifactStatus.REJECTED,
        created_at=created_at or datetime.now(UTC),
        snapshot_id=snapshot.snapshot_id,
        snapshot_status=snapshot.status,
        snapshot=snapshot,
        pacific_date=spec.pacific_date.isoformat(),
        music_spec=spec,
        model=adapter.provenance,
        candidates=candidate_artifacts,
        selected_candidate_id=selected.candidate_id if selected else None,
    )
    write_json(destination / "manifest.json", manifest.model_dump(mode="json"))
    return destination


def approve_artifact(*, root: Path, artifact_id: str, reviewer: str) -> CurrentArtifactPointer:
    """Promote one reviewed artifact. Every eligibility condition is explicit."""
    if not reviewer.strip():
        raise ValueError("a named human reviewer is required for promotion")

    matches = list(root.glob(f"*/{artifact_id}/manifest.json"))
    if len(matches) != 1:
        raise FileNotFoundError(f"could not find exactly one artifact manifest for {artifact_id}")
    manifest_path = matches[0]
    manifest = ArtifactManifest.model_validate_json(manifest_path.read_text())
    if manifest.status != ArtifactStatus.PENDING_REVIEW:
        raise ValueError("only pending artifacts can be approved")
    if manifest.snapshot_status != SnapshotStatus.VERIFIED:
        raise ValueError("illustrative snapshots must never be promoted")
    if not manifest.model.release_eligible:
        raise ValueError("the model release has not been approved for publication")
    if not manifest.selected_candidate_id:
        raise ValueError("no candidate passed the automated evaluation")
    selected = next(
        candidate for candidate in manifest.candidates if candidate.candidate_id == manifest.selected_candidate_id
    )
    if not selected.evaluation.passed:
        raise ValueError("the selected candidate did not pass evaluation")

    approved_at = datetime.now(UTC)
    approved = manifest.model_copy(
        update={
            "status": ArtifactStatus.APPROVED,
            "human_reviewer": reviewer.strip(),
            "approved_at": approved_at,
        }
    )
    write_json(manifest_path, approved.model_dump(mode="json"))
    pointer = CurrentArtifactPointer(
        artifact_id=approved.artifact_id,
        manifest_file=str(manifest_path.relative_to(root)),
        manifest_sha256=sha256_file(manifest_path),
        snapshot_id=approved.snapshot_id,
        approved_at=approved_at,
    )
    write_json(root / "current.json", pointer.model_dump(mode="json"))
    return pointer


def rank_score(evaluation: EvaluationResult) -> float:
    """Deterministic transparent ranking after hard safety gates have passed."""
    metrics = evaluation.metrics
    return round(
        (metrics.target_alignment * 100)
        - (metrics.negative_alignment * 50)
        - (metrics.vocal_probability * 50)
        - abs(metrics.integrated_lufs + 16),
        6,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1_048_576), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)
