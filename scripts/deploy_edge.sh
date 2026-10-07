#!/usr/bin/env bash
# Edge device deployment script — run ON the edge device (Raspberry Pi / Intel N100 etc).
# Not executed as part of this build; provided for later real hardware deployment.
set -euo pipefail

IMAGE_TAG="${1:-vishwasedge/edge:latest}"

echo "Pulling ${IMAGE_TAG}..."
docker pull "${IMAGE_TAG}"

echo "Starting VishwasEdge (offline mode, 4GB memory budget)..."
docker run -d \
  --name vishwasedge-edge \
  --restart unless-stopped \
  -p 8000:8000 \
  -e OFFLINE_MODE=true \
  -e MAX_MEMORY_MB=4096 \
  -e MAX_CPU_PERCENT=80 \
  -v vishwasedge_data:/app/data \
  --read-only \
  --tmpfs /tmp \
  "${IMAGE_TAG}"

echo "Deployed. Health check: curl http://localhost:8000/health"
