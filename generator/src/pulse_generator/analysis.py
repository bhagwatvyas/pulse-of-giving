"""Contract boundary for technical and semantic audio analysis."""

from __future__ import annotations

from typing import Protocol

from .domain import CandidateAnalysis, CandidateMetrics, GeneratedCandidate, MusicSpec


class CandidateAnalyzer(Protocol):
    def analyze(self, candidate: GeneratedCandidate, spec: MusicSpec) -> CandidateAnalysis:
        """Return measurements for one rendered candidate."""


class FixtureMetricsAnalyzer:
    """Deterministic test-only scores; it never inspects the WAV file.

    A production implementation will combine audio analysis (duration, loudness, peak,
    clipping, voice activity) with semantic audio/text evaluation.
    """

    def analyze(self, candidate: GeneratedCandidate, spec: MusicSpec) -> CandidateAnalysis:
        index = int(candidate.effective_parameters["candidate_index"])
        if index == 0:
            metrics = CandidateMetrics(
                duration_seconds=spec.duration_seconds,
                integrated_lufs=-16.0,
                true_peak_dbtp=-1.5,
                vocal_probability=0.01,
                target_alignment=0.78,
                negative_alignment=0.08,
                clipping_detected=False,
            )
        else:
            # A repeatable failed candidate proves that the selection gate is active.
            metrics = CandidateMetrics(
                duration_seconds=spec.duration_seconds,
                integrated_lufs=-16.0,
                true_peak_dbtp=-1.5,
                vocal_probability=0.32,
                target_alignment=0.61,
                negative_alignment=0.30,
                clipping_detected=False,
            )
        return CandidateAnalysis(
            measurement_origin="fixture metrics only; no media analysis was performed",
            metrics=metrics,
        )


class PendingAnalysis:
    """Records a model render without inventing quality or semantic measurements.

    This is intentionally useful only for a local listening session. It prevents a
    raw model output from becoming eligible for publication before the actual audio
    analysis stack is installed and run.
    """

    def analyze(self, candidate: GeneratedCandidate, spec: MusicSpec) -> CandidateAnalysis:
        return CandidateAnalysis(
            measurement_origin="generation recorded; automated audio analysis not yet run",
        )
