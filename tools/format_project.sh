#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

python -m ruff check --fix .
python -m ruff format .
npx prettier --write "src/web/**/*.{html,js,css}" "src/config/**/*.json" MANIFEST.json
python tools/check_project.py
