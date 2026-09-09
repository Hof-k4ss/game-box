#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required." >&2
  exit 1
fi

bundle="${1:-offline/gamebox-images.tar}"
if [ ! -f "$bundle" ]; then
  echo "Image bundle not found: $bundle" >&2
  exit 1
fi

echo "Loading Docker images from $bundle"
docker load -i "$bundle"

echo "Starting GameBox"
docker compose up -d

echo
printf 'GameBox containers started. Check status with: docker compose ps\n'
