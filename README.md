# Pulse of Giving

Pulse of Giving turns a verified Pacific Northwest blood-supply update into a calming daily music artifact, then helps a hesitant visitor take a trusted next step toward donating.

This is an open-source portfolio project about reliable AI application engineering: provenance-aware data, constrained music generation, automated audio evaluation, reproducible artifacts, and a public experience that never confuses a new track with new supply data.

## Product boundary

- **Primary user:** a potential first-time or hesitant donor.
- **Conversion:** an outbound handoff to a recognized blood organization—not health-data collection or appointment scheduling.
- **Initial geography:** the Bloodworks Northwest service footprint, once an authorized source is available.
- **Data rule:** supply data and music-generation time are separate clocks.

## Architecture

```text
Versioned supply snapshot  →  MusicSpec compiler  →  self-hosted model candidates
        ↓                        ↓                        ↓
provenance + freshness       fixed daily seed        automated evaluation
                                                           ↓
website ← current approved manifest ← immutable audio + scores
```

The date makes the composition vary; it never makes the supply data look newer. Every artifact records its snapshot ID, Pacific generation date, model version, prompt/spec, candidate scores, and output hash.

## Repository layout

```text
dist/                    Static public website
generator/               Typed snapshot → MusicSpec compiler and quality policy
infra/cloud-run/         Future Cloud Run GPU Job configuration
.github/workflows/       CI only; no automatic cloud deployment
```

## Local-first roadmap

1. Run the policy/compiler tests locally.
2. Install Docker Desktop and build the lightweight worker image.
3. Exercise the review-only fixture adapter and inspect its artifact manifest.
4. Add and benchmark one pinned, self-hosted model adapter locally.
5. Run a manual Cloud Run GPU Job with synthetic data.
6. Enable the daily schedule only after reviewing output, logs, and cost.

The repository deliberately does **not** include model weights, generated audio, cloud credentials, API tokens, or production data.

## Current status

The website is ready for a review-only staging deployment. It never synthesizes browser audio or substitutes an illustrative scenario for real community data. Instead, it reads `current.json`, rejects any manifest that is not verified, release-eligible, evaluated, and human-approved, verifies the selected audio hash before playback, and otherwise presents a clear not-published state. The generator service compiles a deterministic `MusicSpec`, writes immutable candidate artifacts, and enforces a manual promotion gate. Its included fixture adapter produces test tones only; it does not perform AI inference and cannot publish an artifact. A pinned self-hosted model adapter is the next integration.

## Hosting architecture

The initial deployment keeps the static visitor experience separate from scheduled generation:

```text
Firebase Hosting (dist/)  ←  current.json + immutable approved artifacts
                                      ↑
                         Cloud Storage publication prefix
                                      ↑
Cloud Run GPU Job → self-hosted model → evaluation → human approval
```

`firebase.json` is checked in for a staging deployment. It disables caching for `current.json` and the runtime artifact-origin configuration, while the public player remains disabled until a real approved artifact exists. The repository intentionally does not contain a Firebase project ID, GCP credentials, or deployment tokens.

The Firebase project binding is tracked in `.firebaserc`. Deploy first to a Firebase preview channel. Preview URLs are shareable but not access-controlled, so do not treat one as private or attach a production custom domain until the page has been reviewed with a verified, human-approved artifact.

## Local artifact-pipeline exercise

From `generator/`, after installing the package in editable mode:

```bash
pulse-artifact fixture \
  --snapshot fixtures/illustrative-pnw.json \
  --date 2026-11-02 \
  --out local-artifacts
```

This writes a dated artifact directory with two fixture WAV candidates, file hashes, generation parameters, fixture measurements, evaluation results, and a `pending_human_review` manifest. It deliberately does not write `current.json`: illustrative data and a test-only adapter can never become public playback.

The same local contract can be checked in the worker image:

```bash
docker build -t pulse-generator-local generator
docker run --rm --user "$(id -u):$(id -g)" \
  -v "$(pwd)/generator:/workspace" \
  --entrypoint pulse-artifact \
  pulse-generator-local fixture \
  --snapshot fixtures/illustrative-pnw.json \
  --date 2026-11-02 \
  --out /workspace/local-artifacts
```

## Open source

Released under the [MIT License](LICENSE). Contributions, security reporting, community expectations, and model-admission policy are described in [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [MODEL_INTEGRATION.md](MODEL_INTEGRATION.md).

## Attribution and source boundaries

This project must only describe inventory or donor-need signals using a permitted, timestamped source. An illustrative fixture is included solely for engineering tests. It is not a real blood-supply report.
