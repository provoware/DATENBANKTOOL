#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "PROVOWARE DATENBANKTOOL · P0-012 Browser-Endabnahme"
echo "====================================================="

if ! command -v google-chrome >/dev/null 2>&1 && ! command -v google-chrome-stable >/dev/null 2>&1; then
  echo "🔴 Google Chrome wurde nicht gefunden."
  echo "Tipp: Chrome installieren und dieses Skript danach erneut starten."
  exit 2
fi

if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "🔴 Node.js und npm werden für den Browser-Test benötigt."
  exit 2
fi

if [ ! -d node_modules/@playwright/test ]; then
  echo "🟡 Browser-Testwerkzeuge werden lokal installiert …"
  npm install --ignore-scripts
fi

export PROVOWARE_DB_PATH="${PROVOWARE_DB_PATH:-$ROOT_DIR/runtime/p0-012-browser.sqlite3}"
mkdir -p "$(dirname "$PROVOWARE_DB_PATH")"

echo "🟣 Automatischer Chrome-Smoke startet."
echo "Datenbank: $PROVOWARE_DB_PATH"
npm run browser:smoke:chrome

echo
printf '%s\n' "🟢 Automatischer Chrome-Smoke bestanden."
printf '%s\n' "Wichtig: Danach die manuelle KDE-/Zoom-Matrix in docs/BROWSER_ABNAHME.md abarbeiten."
