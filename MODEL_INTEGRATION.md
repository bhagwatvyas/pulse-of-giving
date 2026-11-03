# Hosted model integration policy

The generation worker will use a self-hosted model. A third-party music-generation API is out of scope.

## Before a model can publish audio

1. Record the exact model ID, revision/hash, upstream license, and reviewed date.
2. Run the same container locally with an illustrative snapshot.
3. Generate a small, human-reviewed evaluation set.
4. Confirm the model can respect the instrumental-only and calm-mood policy.
5. Configure technical and semantic evaluators before enabling publication.

## Adapter contract

The model adapter receives a `MusicSpec` and returns one or more candidate audio paths. It must honor the spec's seed where the model supports it, and it must emit the effective generation parameters alongside each candidate.

The adapter must expose immutable `ModelProvenance`: model ID, revision, upstream license, review date, and a release-eligibility flag. The production worker records that provenance in every manifest. A model is not publication-eligible just because it can create audio.

The repository includes a `FixtureToneAdapter` for local contract tests. It writes deterministic WAV tones; it is not AI music, does not perform inference, and is permanently ineligible for publication.

## Required rejection gates

- 30–40 second duration
- -20 to -14 LUFS integrated loudness
- no peak above -1 dBTP
- no detected clipping
- low vocal/speech probability
- sufficient semantic alignment with the calm instrumental target
- low similarity to the forbidden-quality prompt

The evaluator ranks candidates; it does not prove that music is calm for every listener. The first public phase requires human approval before publication.

## Artifact promotion policy

Each run writes an immutable directory containing `manifest.json`, candidate audio, hashes, effective parameters, measurements, and evaluation decisions. A `current.json` pointer is written only after all of the following are true:

1. The source snapshot is verified—not illustrative.
2. The exact model revision is marked release-eligible after review.
3. The selected candidate passes every automatic rejection gate.
4. A named human reviewer explicitly approves the run.

The public website will read only `current.json`; it must never infer freshness from an audio creation time.
