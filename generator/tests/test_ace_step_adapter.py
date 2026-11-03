from pulse_generator.ace_step_adapter import AceStepApiAdapter


def test_ace_step_provenance_is_deliberately_not_release_eligible() -> None:
    adapter = AceStepApiAdapter(
        endpoint="http://127.0.0.1:8000",
        model_id="acestep-v15-turbo",
        revision="test-commit",
        reviewed_at="2026-11-02",
    )

    assert adapter.provenance.model_id == "acestep-v15-turbo"
    assert adapter.provenance.release_eligible is False


def test_ace_step_accepts_common_api_response_shapes() -> None:
    assert AceStepApiAdapter._task_id({"data": {"task_id": "job-1"}}) == "job-1"
    assert (
        AceStepApiAdapter._audio_path(
            {"result": '[{"file":"/tmp/outputs/a.wav", "status":1}]'}
        )
        == "/tmp/outputs/a.wav"
    )


def test_ace_step_parses_batched_query_response() -> None:
    assert AceStepApiAdapter._query_result(
        {"data": [{"task_id": "job-1", "status": 1, "result": "[]"}]}, "job-1"
    ) == {"task_id": "job-1", "status": 1, "result": "[]"}
