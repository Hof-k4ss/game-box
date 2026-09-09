#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "== GameBox diagnostic =="
echo

if [ ! -d roms ]; then
  echo "ERROR: roms/ directory is missing"
  exit 1
fi

echo "Host ROM directories:"
find roms -maxdepth 2 -type d -print | sort

echo

echo "Host ROM files:"
find roms -type f -printf '%p (%s bytes)\n' | head -50 || true
echo

echo "Docker containers:"
docker compose ps || true
echo

echo "Inside RomM container (/romm/library):"
if docker inspect gamebox >/dev/null 2>&1; then
  docker exec gamebox sh -lc 'ls -la /romm/library; echo; ls -la /romm/library/roms 2>/dev/null || true; echo; find /romm/library/roms -maxdepth 2 -type f 2>/dev/null | head -50 || true'
else
  echo "Container gamebox does not exist."
fi

echo
printf 'If /romm/library/roms is empty while host roms/ contains files, the bind mount is not the running compose configuration.\n'
printf 'After fixing the mount, use RomM Library -> Scan -> Quick Scan.\n'
