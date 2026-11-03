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
Versioned supply snapshot  →  MusicSpec compiler  →  hosted model candidates
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
3. Add and benchmark one pinned ACE-Step model adapter locally.
4. Run a manual Cloud Run GPU Job with synthetic data.
5. Enable the daily schedule only after reviewing output, logs, and cost.

The repository deliberately does **not** include model weights, generated audio, cloud credentials, API tokens, or production data.

## Current status

The website is an illustrative front-end prototype. The generator service currently compiles a deterministic `MusicSpec` and quality policy from a typed snapshot. It does not publish audio until a pinned hosted-model adapter has been validated locally.

## Open source

Released under the [MIT License](LICENSE). Contributions, security reporting, community expectations, and model-admission policy are described in [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [MODEL_INTEGRATION.md](MODEL_INTEGRATION.md).

## Attribution and source boundaries

This project must only describe inventory or donor-need signals using a permitted, timestamped source. An illustrative fixture is included solely for engineering tests. It is not a real blood-supply report.
