#!/usr/bin/env bash
# This VM exists only for one review-only render. It shuts down whether the
# render succeeds or fails so it cannot become an unattended GPU expense.
set -euo pipefail

readonly PROJECT_ID="project-21d53579-0ef7-4425-b34"
readonly IMAGE="us-central1-docker.pkg.dev/${PROJECT_ID}/pulse/ace-step-render@sha256:455bc82fdc6f9dd4f3b51907e265c9297d7afdf69d25116d581bec1c03c18555"

finish() {
  status="$?"
  shutdown -h now || true
  exit "$status"
}
trap finish EXIT

gcloud auth configure-docker us-central1-docker.pkg.dev --quiet
docker pull "$IMAGE"
docker run --rm --gpus all "$IMAGE" \
  --snapshot /workspace/generator/fixtures/illustrative-pnw.json \
  --bucket "${PROJECT_ID}-pulse-artifacts" \
  --revision ca1e85fe9430179831e6bc6be790c332190a3866 \
  --date 2026-11-02
