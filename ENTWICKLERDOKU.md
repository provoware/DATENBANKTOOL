# Entwicklerdokumentation

## Architekturziel

DATENBANKTOOL wird in klar getrennten Schichten entwickelt:

1. **Analyse-Kern** – liest Dateisystemdaten und erzeugt neutrale Modelle.
2. **Persistenter Index** – speichert große Bestände inkrementell und reparierbar.
3. **Planungsengine** – erzeugt unveränderliche Änderungspläne ohne sie auszuführen.
4. **Validierung** – prüft Rechte, Speicherplatz, Konflikte und Dateisystemgrenzen.
5. **Transaktionsengine** – führt bestätigte Pläne journalbasiert aus.
6. **Wiederherstellung** – Undo, Quarantäne und Reparatur nach Abbruch.
7. **Oberfläche** – Einfach-, Geführt- und Expertenmodus ohne eigenen Dateisystemzugriff.

Die Oberfläche darf niemals direkt Dateien verändern. Jede spätere Änderung muss über Plan, Validierung, Journal und Ergebnisprüfung laufen.

## Aktueller Quellaufbau

- `src/datenbanktool/cli.py`: Kommandozeilenoberfläche und sichere Berichtsausgabe.
- `src/datenbanktool/core/models.py`: neutrale Datenmodelle.
- `src/datenbanktool/core/classification.py`: Dateikategorien.
- `src/datenbanktool/core/naming.py`: nicht destruktive Dateinamenprüfung.
- `src/datenbanktool/core/scanner.py`: rein lesender Scanner und optionale Hashprüfung.
- `project_registry.json`: Version, Phase, Sicherheitsvorgaben und Modulstatus.

## Sicherheitsverträge

### Scanner

- verändert keine gescannten Dateien;
- folgt symbolischen Verzeichnissen standardmäßig nicht;
- protokolliert Einzelfehler;
- sortiert Ergebnislisten deterministisch;
- aktiviert Inhalts-Hashing nur ausdrücklich;
- darf später Scanfortschritt liefern, aber keine UI-Abhängigkeit erhalten.

### Berichtsausgabe

- UTF-8 und maschinenlesbar;
- atomarer Austausch über temporäre Datei;
- vorhandene Zieldatei wird ohne ausdrückliche Freigabe nicht ersetzt;
- Berichtsfehler dürfen keine Originaldaten verändern.

### Künftige Dateioperationen

Eine Operation darf erst freigeschaltet werden, wenn mindestens folgende Nachweise vorhanden sind:

1. vollständiges Planmanifest;
2. Vorher-Nachher-Vorschau;
3. Kollisions- und Rechteprüfung;
4. Speicherplatzprüfung;
5. transaktionales Journal;
6. idempotente Wiederaufnahme;
7. Undo-Manifest;
8. Quarantäne statt Direktlöschung;
9. automatisierte Abbruch- und Recoverytests.

## Versionierung

Die Projektversion wird in `project_registry.json`, `pyproject.toml` und `src/datenbanktool/__init__.py` konsistent geführt. In einer späteren Iteration soll eine einzige Quelldatei alle Versionsangaben generieren und validieren.

## Qualitätsprüfungen

Aktuell:

```bash
python -m compileall -q src tests
PYTHONPATH=src python -m unittest discover -s tests -v
```

Geplant:

```bash
ruff check .
mypy src
bandit -r src
pip-audit
coverage run -m unittest discover -s tests
coverage report --fail-under=80
```

## Entwicklungsregeln

- Neue Funktionen zuerst als Datenmodell und Vertrag beschreiben.
- Analyse und schreibende Operationen strikt trennen.
- Keine stillen Korrekturen oder Löschentscheidungen.
- Große Bestände streamend oder indexbasiert verarbeiten.
- Fehlerpfade gleichwertig zu Erfolgspfaden testen.
- Benutzertexte müssen Ursache, Wirkung und sichere Handlung nennen.
- Änderungen an bestehenden Dateien klein und positionsgenau halten.
- `AGENTS.md` bleibt in dieser Iteration unverändert.

## Nächste Architekturiteration

Der nächste technische Schritt ist ein SQLite-Index mit Schema-Version, Migration, Batch-Import, Transaktionen und Wiederaufnahme. Erst danach sollte die grafische Oberfläche aufgesetzt werden, damit diese nicht auf flüchtigen In-Memory-Daten basiert.
