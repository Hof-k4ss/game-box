#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required." >&2
  exit 1
fi

mkdir -p offline/images data

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Review secrets before continuing."
fi

set -a
. ./.env
set +a

images=(
  "${ROMM_IMAGE:-rommapp/romm:latest}"
  "${MARIADB_IMAGE:-mariadb:11}"
  "${VALKEY_IMAGE:-valkey/valkey:8}"
)

for image in "${images[@]}"; do
  echo "Pulling $image"
  docker pull "$image"
done

bundle="offline/gamebox-images.tar"
rm -f "$bundle"
docker save "${images[@]}" -o "$bundle"

echo
printf 'Offline image bundle created: %s\n' "$bundle"
printf 'Copy the repository plus this bundle to the isolated machine, then run scripts/import-offline.sh.\n'
