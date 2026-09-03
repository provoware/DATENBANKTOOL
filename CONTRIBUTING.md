# Mitentwickeln

## Vor jeder Änderung

```bash
python -m ruff check .
python -m ruff format --check .
npx prettier --check .
pytest -q
python tools/check_project.py
```

## Commit-Regel

Ein Commit sollte einen klaren fachlichen Zweck haben. Keine Nutzerdaten, Logs, temporären Dateien oder Secrets committen.

## Pull Request

Beschreibe:

- Was wurde geändert?
- Warum?
- Welche Risiken gibt es?
- Welche Tests liefen?
- Welche Regressionen wurden geprüft?
- Ist Dokumentation/TODO aktualisiert?
