from .domain import CandidateMetrics, EvaluationResult


def evaluate_candidate(metrics: CandidateMetrics) -> EvaluationResult:
    reasons: list[str] = []
    if not 30 <= metrics.duration_seconds <= 40:
        reasons.append("duration outside 30-40 second window")
    if not -20 <= metrics.integrated_lufs <= -14:
        reasons.append("loudness outside calming playback range")
    if metrics.true_peak_dbtp > -1:
        reasons.append("true peak exceeds -1 dBTP")
    if metrics.vocal_probability > 0.08:
        reasons.append("vocal probability exceeds instrumental-only threshold")
    if metrics.target_alignment < 0.55:
        reasons.append("insufficient alignment with target calm-music description")
    if metrics.negative_alignment > 0.22:
        reasons.append("too similar to excluded audio qualities")
    if metrics.clipping_detected:
        reasons.append("clipping detected")
    return EvaluationResult(passed=not reasons, reasons=reasons, metrics=metrics)
