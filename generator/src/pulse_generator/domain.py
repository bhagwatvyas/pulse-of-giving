from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import AnyHttpUrl, BaseModel, Field, model_validator


class SnapshotStatus(StrEnum):
    ILLUSTRATIVE = "illustrative"
    VERIFIED = "verified"


class SupplyState(StrEnum):
    STEADY = "steady"
    NEEDS_SUPPORT = "needs_support"
    HIGH_NEED = "high_need"


class CommunityPulseSnapshot(BaseModel):
    snapshot_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{4,80}$")
    status: SnapshotStatus
    coverage_area: str = Field(min_length=3, max_length=120)
    published_at: datetime
    valid_until: datetime
    supply_state: SupplyState
    source_name: str = Field(min_length=3, max_length=120)
    source_url: AnyHttpUrl

    @model_validator(mode="after")
    def expiry_is_after_publication(self) -> "CommunityPulseSnapshot":
        if self.valid_until <= self.published_at:
            raise ValueError("valid_until must be later than published_at")
        return self


class MusicSpec(BaseModel):
    snapshot_id: str
    snapshot_status: SnapshotStatus
    pacific_date: date
    seed: int = Field(ge=0, le=2**63 - 1)
    model_id: str
    duration_seconds: int = Field(ge=25, le=50)
    tempo_bpm: int = Field(ge=64, le=80)
    prompt: str
    negative_prompt: str
    safety_constraints: list[str]


class ModelProvenance(BaseModel):
    """Identity and review state for the exact self-hosted model release."""

    model_id: str = Field(min_length=3, max_length=200)
    revision: str = Field(min_length=3, max_length=200)
    upstream_license: str = Field(min_length=3, max_length=200)
    reviewed_at: date
    release_eligible: bool = False


class GeneratedCandidate(BaseModel):
    """A candidate emitted by a model adapter before it is evaluated."""

    candidate_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{2,80}$")
    audio_path: Path
    effective_parameters: dict[str, Any]


class CandidateMetrics(BaseModel):
    duration_seconds: float
    integrated_lufs: float
    true_peak_dbtp: float
    vocal_probability: float = Field(ge=0, le=1)
    target_alignment: float = Field(ge=0, le=1)
    negative_alignment: float = Field(ge=0, le=1)
    clipping_detected: bool


class EvaluationResult(BaseModel):
    passed: bool
    reasons: list[str]
    metrics: CandidateMetrics | None = None


class CandidateAnalysis(BaseModel):
    """Measurements supplied by a pluggable audio-analysis implementation."""

    measurement_origin: str = Field(min_length=3, max_length=240)
    metrics: CandidateMetrics | None = None
