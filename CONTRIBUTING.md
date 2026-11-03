# Contributing

Keep supply claims traceable to a permitted, timestamped source. Do not commit donor, patient, health, appointment, credential, model-weight, or generated-audio data.

Add tests for policy, freshness, or prompt-spec changes. Preserve the distinction between data freshness and music-generation time.

Run tests from `generator/`:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
```

The default suite does not download a model or require a GPU.
