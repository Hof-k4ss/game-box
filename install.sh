#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

if ! command -v docker >/dev/null 2>&1; then
  echo "❌ Docker n'est pas installé. Installe Docker Engine + Docker Compose puis relance ce script."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "❌ Docker Compose n'est pas disponible."
  exit 1
fi

mkdir -p roms/_a_trier bios
chmod +x gamebox

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "✅ .env créé."
  echo ""
  echo "👉 Ouvre maintenant .env et indique le dossier où se trouvent tes ROMs."
  echo "   Exemple : $HOME/Téléchargements/ROMs"
  echo ""
fi

echo "✅ GameBox est prêt."
echo "   1. Vérifie .env"
echo "   2. Lance : ./gamebox start"
echo "   3. Puis : ./gamebox import"
