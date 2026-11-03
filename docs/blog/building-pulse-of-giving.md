---
title: "Building Pulse of Giving: A Calmer Path from Data to Donation"
description: "Why I am building an AI-generated daily soundscape around blood donation—and the reliability constraints behind it."
status: draft
---

# Building Pulse of Giving: A Calmer Path from Data to Donation

Blood donation can feel bigger and more frightening than it is. The equipment is unfamiliar, eligibility rules can feel opaque, and the need itself is often presented as an alarming statistic. I wanted to build something that moves in the other direction: a small, calming experience that helps someone understand the need in their community, see that donation is manageable, and take a trusted next step.

This is personal for me. My wife went through plasmapheresis, and another person's blood donation quite literally helped save her life. That experience made the generosity behind donated blood impossible to treat as an abstraction. It also made me think about the gap between the quiet, ordinary act of donating and the extraordinary consequence it can have for a family.

That is the reason for **Pulse of Giving**: an experience that turns a verified regional blood-supply update into a short, calm instrumental piece, then hands the visitor to established blood organizations to learn more or find a donation center.

The product is not trying to become a blood bank, a scheduling platform, or a dashboard that turns scarcity into spectacle. Its job is narrower: make the first step feel human and doable.

## The product idea: make the signal felt, without manufacturing urgency

The central idea is not “music about blood donation.” The data itself should influence the music.

Each generation begins with a regional supply snapshot. The snapshot is classified into a deliberately small set of states—steady, needs support, or high need. That state adjusts a constrained music specification: for example, tempo, harmonic color, and texture. The composition remains warm and instrumental in every state. A higher-need state can be a little more spacious or unresolved, but it should never become anxious, dramatic, or manipulative.

That constraint matters. A public-interest product should not make people feel guilty or frightened in order to earn a click. The music is there to create a moment of reflection and calm, not to simulate an emergency.

The site then pairs the listening experience with the practical questions a prospective donor may actually have:

- What happens at an appointment?
- How much time should I plan for?
- What should I do before I donate?
- Where can I get authoritative eligibility guidance?
- Where can I find a legitimate local donation organization?

The call to action is intentionally outbound. Pulse of Giving should point people toward organizations that already operate collection, screening, scheduling, and clinical care. Building a second scheduling layer would add risk without adding much value.

## The hard part is not generating audio

Generating a pleasant 35-second clip is feasible. Building a system that deserves to make a public claim about a community’s blood supply is the actual engineering problem.

I made four decisions early:

1. **Data freshness and music freshness are separate clocks.** A new track generated today does not imply that the supply data was published today. Every artifact records both the source snapshot and the Pacific-date generation seed. The UI must never describe a track as “live” unless the underlying source genuinely is.

2. **The system fails closed.** If a verified, review-approved artifact is unavailable, the site does not substitute a plausible number, a synthetic trend, or browser-generated audio. It displays a clear unpublished state instead.

3. **Audio generation is self-hosted.** The project uses a containerized ACE-Step model integration instead of a third-party music-generation API. That makes model versioning, reproducibility, and the deployment path visible parts of the engineering work.

4. **Publication is a promotion, not a side effect of inference.** A model output is only a candidate. It cannot become public playback until the data, model release, automated evaluation, and human review gates all pass.

Those choices are not incidental implementation details. They shape the product’s credibility.

## The architecture

The system is divided into a public static experience and a private generation pipeline.

```text
Verified PNW source snapshot
            │
            ▼
     Deterministic MusicSpec compiler
            │
            ▼
 Self-hosted ACE-Step GPU worker
            │
            ▼
 Candidate analysis + rejection gates
            │
            ▼
 Immutable artifact manifest + WAV candidates
            │
      human approval
            ▼
     current.json pointer ───► Firebase-hosted web experience
```

The frontend is deliberately simple. It is a static Firebase-hosted site that reads a small `current.json` pointer, resolves an immutable manifest, and downloads audio only after a visitor presses play. Before playback, the browser verifies the audio file’s SHA-256 against the manifest. That does not make a public bucket a security boundary, but it does prevent an accidental file replacement from silently changing the sound users hear.

The generator is a typed Python service. Its input is a `CommunityPulseSnapshot`, which includes the source identity, source URL, coverage area, publication time, validity window, and verification status. The compiler turns that snapshot into a deterministic `MusicSpec`:

- a date-derived seed;
- a fixed duration window;
- a tempo constrained to a calm range;
- an instrumental prompt;
- a negative prompt excluding lyrics, sirens, aggressive drums, harsh percussion, and abrupt endings; and
- explicit safety constraints recorded alongside the result.

The date is intentionally part of the seed. That gives the project a new composition cadence without pretending the underlying data changes every day.

## A model adapter, not a model-shaped abstraction

The music model sits behind an adapter contract. The adapter receives a `MusicSpec`, renders one or more candidates, and returns the effective parameters used for each one: prompt, seed, BPM, duration, model identifier, and pinned upstream revision.

That contract has a few benefits:

- The rest of the pipeline does not depend on one model’s HTTP API.
- Each candidate is traceable to the precise inputs that produced it.
- A fixture adapter can exercise the artifact lifecycle in local tests without downloading model weights or spending GPU time.
- A real adapter can be tested locally, then run in a GPU job without changing the artifact semantics.

For the first self-hosted integration, I am using ACE-Step’s Turbo profile in a containerized GPU worker. The worker starts the model API on a loopback interface, submits a single constrained generation request, polls it to completion, and writes the output into a dated artifact directory. The public site never talks directly to the model service.

This is also why the GPU deployment is intentionally one-shot. A long-running public inference endpoint would be the wrong operational shape for a daily artifact pipeline: it costs money while idle, expands the attack surface, and implies real-time behavior the product does not need. The better shape is a job that starts, generates candidates, uploads a private review artifact, and exits.

## Provenance is part of the artifact

Every generation produces an immutable manifest instead of a bare audio file. The manifest captures:

- the complete source snapshot and its verification status;
- the music specification and generation date;
- model ID, pinned revision, license, and release-review state;
- candidate file paths and SHA-256 hashes;
- effective model parameters;
- analysis origin, metrics, and rejection reasons; and
- the selected candidate and human reviewer, if the artifact is approved.

There is no shortcut from “file exists” to “file is public.” The only artifact the frontend accepts is one reached through an approved `current.json` pointer. Promotion rejects illustrative source data, an unreviewed model release, missing automated evaluation, a failing candidate, or an unnamed reviewer.

This is intentionally conservative. A project that talks about blood donation should be more careful with data provenance than a typical generative-media demo.

## Quality evaluation: never invent a score

The pipeline has technical rejection gates for duration, integrated loudness, true peak, clipping, vocal probability, target alignment, and similarity to excluded qualities. Those are useful only when measured by a real analysis stack.

One important rule in the implementation is that unavailable analysis is recorded as unavailable. It is not filled with plausible-looking values. A genuine model render can be stored for private listening while remaining in `pending_human_review`; it cannot be promoted merely because the audio file was successfully created.

That distinction is easy to miss in an AI application. Model output, evaluation output, and a production decision are different things. Keeping them separate makes both the system and the story more credible.

## What is intentionally not live yet

The current project uses an illustrative Pacific Northwest fixture for end-to-end engineering work. It is clearly marked illustrative and structurally prevented from becoming public playback.

That is not a temporary wording problem. It is a product requirement. Before the site presents current community need, it needs a source with an appropriate update cadence, a documented interpretation of what the source measures, and an ingestion path that preserves the source’s timestamps and provenance. Until then, the website should say less—not infer more.

Similarly, self-hosting a model does not make it automatically appropriate for public use. The model’s exact revision, license, output behavior, and evaluation results need explicit review before a release-eligible artifact exists.

## The engineering standard I want this project to represent

Pulse of Giving is a public-interest project, but it is also a systems project. I want it to demonstrate a version of AI engineering that is less interested in a flashy one-off demo and more interested in the details that let a system earn trust:

- model outputs that are reproducible and inspectable;
- data claims that match what the source actually says;
- immutable artifacts instead of mutable “latest” files;
- graceful degradation instead of fabricated fallbacks;
- explicit human review where automated judgment is not enough; and
- cloud infrastructure that runs only when it has work to do.

The music is the invitation. The reliable pipeline behind it is the promise.

If this project helps one hesitant person feel more at ease about donating, it will have done something worthwhile. And if it can show that AI systems can be built with warmth, restraint, and operational rigor at the same time, that is a standard worth carrying into other work too.
