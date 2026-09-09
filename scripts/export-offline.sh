#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ARCHIVE="${1:-gamebox-offline.tar.gz}"

if [ ! -f offline/gamebox-images.tar ]; then
  echo "offline/gamebox-images.tar is missing. Run prepare-offline.sh first." >&2
  exit 1
fi

mkdir -p "$(dirname "$ARCHIVE")"

tar -czf "$ARCHIVE" \
  --exclude='./.git' \
  --exclude='./data/mariadb' \
  --exclude='./data/valkey' \
  --exclude='./data/romm' \
  --exclude='./data/assets' \
  --exclude='./data/resources' \
  --exclude='./roms/*' \
  --exclude='./offline/*.tar.zst' \
  .

echo "Offline GameBox bundle exported to $ARCHIVE"
echo "ROMs are intentionally excluded; copy your local, legally obtained library separately."
