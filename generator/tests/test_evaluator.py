from pulse_generator.domain import CandidateMetrics
from pulse_generator.evaluator import evaluate_candidate


def test_good_candidate_passes() -> None:
    result = evaluate_candidate(CandidateMetrics(
        duration_seconds=35,
        integrated_lufs=-16,
        true_peak_dbtp=-1.5,
        vocal_probability=.01,
        target_alignment=.73,
        negative_alignment=.09,
        clipping_detected=False,
    ))
    assert result.passed


def test_voice_or_clipping_rejects_candidate() -> None:
    result = evaluate_candidate(CandidateMetrics(
        duration_seconds=35,
        integrated_lufs=-16,
        true_peak_dbtp=.2,
        vocal_probability=.45,
        target_alignment=.73,
        negative_alignment=.09,
        clipping_detected=True,
    ))
    assert not result.passed
    assert len(result.reasons) == 3
