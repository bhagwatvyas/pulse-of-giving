# Experiment 001: Critical Design Review

Status: proposed
Owner: Vyas Bhagwat
Product under test: Pulse of Giving managed generative-music API

## Question

Does an independent reviewing agent improve the quality and reliability of an engineering design enough to justify the additional latency and model cost?

This experiment tests the workflow, not a particular model vendor. Every variant receives the same product brief and must produce an architecture that could support Pulse of Giving as the first customer of a managed generative-media API.

## Product brief

Pulse of Giving needs a managed API that lets a website create a channel with a normalized regional signal, a generation policy, and a cadence. The service should asynchronously generate a calm instrumental edition, expose immutable provenance, and return the latest successful edition through a stable API. A customer should never need to operate GPU inference.

The design must address:

- channel and tenant isolation;
- weekly scheduled generation and idempotency;
- model-adapter boundaries;
- artifact storage and immutable versioning;
- last-good and default-audio fallback;
- automated output safety and format checks;
- API availability, latency, and rate limits;
- observability, cost attribution, and operations;
- authentication, authorization, and abuse controls; and
- a migration path from one internal customer to multiple external customers.

The product must not expose raw blood-supply numbers as medical or operational advice. A signal can shape an edition without being presented as a live clinical claim.

## Variants

Run the same brief through three workflows:

### A — Single-agent design

One agent produces the requirements interpretation, architecture, tradeoffs, and final recommendation in one pass. It may use tools, but it receives no independent review.

### B — Specialized design team

Separate researcher and architect agents produce artifacts against explicit schemas. An orchestrator combines their work into one design. There is no independent adversarial review.

### C — Specialized team plus independent review

The researcher and architect produce the design. A reviewer receives the product brief and design artifacts, but not the architect’s hidden reasoning or self-assessment. The reviewer must identify unsupported assumptions, missing failure modes, requirement gaps, and unvalidated claims. The architect then responds to each finding with evidence, a change, or an explicit accepted tradeoff.

## Required artifacts

Each run must produce the following versioned artifacts:

1. `requirements.json` — interpreted requirements, non-goals, assumptions, and acceptance criteria.
2. `architecture.md` — component boundaries, request flows, data model, deployment, and operations.
3. `tradeoffs.json` — important decisions with alternatives, consequences, and confidence.
4. `review.json` — findings classified as blocker, major, minor, or informational, each with evidence.
5. `decision-record.json` — the final disposition of every review finding.
6. `evaluation.json` — metric results, evaluator notes, cost, latency, and run identifiers.

The orchestrator must reject a run that has missing artifacts, invalid schemas, unresolved blockers, or no evidence for a claimed requirement.

## Reviewer contract

The reviewer is not asked whether the design “looks good.” It must answer:

- Which requirements are not represented in the design?
- Which claims are unsupported by evidence?
- Where can a tenant observe another tenant’s data or artifacts?
- What happens when generation is slow, duplicated, partially successful, or unavailable?
- Can the public API return a safe last-good edition without making a false freshness claim?
- What are the most expensive or operationally fragile components?
- Which decisions should be tested with a prototype before implementation?
- What is the smallest change that would make each blocker resolvable?

Every finding must include a severity, affected artifact section, rationale, and a concrete acceptance test or evidence request.

## Scoring

Score each variant with the same rubric. A score is not accepted without an evaluator note.

| Metric | Measurement |
|---|---|
| Requirement coverage | Required concerns represented and traceable to a component or test |
| Acceptance-test quality | Tests are specific, executable, and able to fail |
| Failure-mode coverage | Important degraded, duplicate, and adversarial paths addressed |
| Unsupported assumptions | Count of claims without evidence or an explicit validation plan |
| Escaped defects | Issues discovered only after the final artifact was declared complete |
| Review yield | Blockers and major findings that changed the design |
| Cost | Model and tool cost per accepted run |
| Latency | Wall-clock time to accepted design |
| Human intervention | Number and duration of required interventions |

The multi-agent workflow is a success only if Variant C improves quality metrics without an unacceptable increase in cost or time. We should record cases where the reviewer is wrong; adversarial disagreement is useful only when it improves decisions.

## Initial acceptance criteria

The final design must demonstrate:

- an idempotent generation job keyed by tenant, channel, and cadence window;
- immutable editions addressed by content hash or equivalent immutable identity;
- a read path that returns the latest successful edition and its provenance;
- explicit fallback semantics for no edition, stale edition, and failed generation;
- a model adapter contract that keeps provider-specific APIs out of the public API;
- tenant-scoped authorization on channels, jobs, and artifacts;
- structured logs, metrics, and traces for ingestion, generation, evaluation, and delivery;
- cost attribution per tenant and channel; and
- a testable deployment and rollback strategy.

## Execution protocol

1. Freeze the product brief and rubric at the start of the experiment.
2. Run Variants A, B, and C with the same model budget and tool access.
3. Store all artifacts and timestamps under a run-specific directory.
4. Score each run using the same evaluator prompt and human spot-check.
5. Compare quality, cost, latency, and intervention metrics.
6. Publish the results and unresolved questions before adding more agent roles.

## Expected output

The immediate output is not production code. It is evidence about whether the workflow improves design quality. If Variant C wins, its contracts become the foundation for the first orchestrator prototype. If it does not, we simplify the workflow and retain only the roles that demonstrate measurable value.
