# Entwicklerdokumentation

## Aufbau

- `registry.json`: verbindlicher Name und Version.
- `src/datenbanktool/core.py`: validierte, ausgabefreie SQLite-Logik.
- `src/datenbanktool/cli.py`: Argumente, Text-/JSON-Ausgabe und Exitcodes.
- `tests/test_cli.py`: fokussierte Integrations- und Logiktests.

Die Kernlogik öffnet Datenbanken ausschließlich über eine SQLite-URI mit `mode=ro`. Benutzerwerte werden nicht in SQL-Text eingesetzt. Neue Ausgabeformen sollen Daten aus `core.py` formatieren, statt Datenbankzugriffe zu duplizieren.

## Schnittstellenvertrag

- Erfolgreiche Befehle liefern Exitcode `0`.
- Validierungs- und Datenbankfehler liefern Exitcode `2`.
- Im JSON-Modus ist ein Fehler ein Objekt mit dem Schlüssel `error`.
- `list_tables` liefert Tabellen und Spalten alphabetisch beziehungsweise in Spaltenreihenfolge.

## Versionierung und Prüfung

Semantische Versionierung wird verwendet: inkompatible Änderung = Hauptversion, neue kompatible Funktion = Nebenversion, Fehlerkorrektur = Patchversion. Nur `registry.json` wird manuell geändert; das Paket liest den Wert daraus.

Vor einem Commit:

```bash
python -m json.tool registry.json >/dev/null
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m datenbanktool --help
```
