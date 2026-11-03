#!/usr/bin/env bash
# This VM exists only for one review-only render. It shuts down whether the
# render succeeds or fails so it cannot become an unattended GPU expense.
set -euo pipefail
readonly LOG_FILE="/var/log/pulse-render-startup.log"
exec > >(tee -a "$LOG_FILE" /dev/ttyS0) 2>&1
set -x

readonly PROJECT_ID="project-21d53579-0ef7-4425-b34"
readonly IMAGE="us-central1-docker.pkg.dev/${PROJECT_ID}/pulse/ace-step-render@sha256:455bc82fdc6f9dd4f3b51907e265c9297d7afdf69d25116d581bec1c03c18555"

finish() {
  status="$?"
  # The VM may shut down before serial output can be retrieved. Preserve the
  # complete boot log as a private, timestamped diagnostic object instead.
  gcloud storage cp "$LOG_FILE" \
    "gs://${PROJECT_ID}-pulse-artifacts/runtime-logs/${HOSTNAME}-$(date +%Y%m%dT%H%M%SZ).log" \
    || true
  sync
  shutdown -h now || true
  exit "$status"
}
trap finish EXIT

echo "Pulse render VM startup: $(date -Is)"
# COS does not ship the driver in the base image. Install the supported driver
# at boot and make its binaries executable before exposing it to Docker.
cos-extensions install gpu
mount --bind /var/lib/nvidia /var/lib/nvidia
mount -o remount,exec /var/lib/nvidia
/var/lib/nvidia/bin/nvidia-smi
command -v docker
docker version
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet
docker pull "$IMAGE"
docker run --rm \
  --volume /var/lib/nvidia/lib64:/usr/local/nvidia/lib64:ro \
  --volume /var/lib/nvidia/bin:/usr/local/nvidia/bin:ro \
  --device /dev/nvidia0:/dev/nvidia0 \
  --device /dev/nvidia-uvm:/dev/nvidia-uvm \
  --device /dev/nvidiactl:/dev/nvidiactl \
  "$IMAGE" \
  --snapshot /workspace/generator/fixtures/illustrative-pnw.json \
  --bucket "${PROJECT_ID}-pulse-artifacts" \
  --revision ca1e85fe9430179831e6bc6be790c332190a3866 \
  --date 2026-11-02
