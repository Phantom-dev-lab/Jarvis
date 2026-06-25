#!/usr/bin/env bash
# Startet Jarvis. Legt bei Bedarf eine virtuelle Umgebung an und installiert
# die Abhängigkeiten.
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "→ Erstelle virtuelle Umgebung (.venv) …"
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "→ Installiere Abhängigkeiten …"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

if [ ! -f ".env" ]; then
  echo "⚠  Keine .env gefunden – kopiere .env.example nach .env."
  echo "   Bitte ANTHROPIC_API_KEY (und optional Home Assistant) eintragen."
  cp .env.example .env
fi

echo "→ Jarvis startet …  http://localhost:${PORT:-8000}"
exec python -m backend.main
