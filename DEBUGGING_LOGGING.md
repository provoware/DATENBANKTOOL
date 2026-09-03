# Debugging- und Logging-Standard

## Ziel

Technische Details für Maschinen und Entwickler, aber eine kurze verständliche Erklärung für Nutzer.

## Zwei Ausgaben

### 1. Maschinenlog

Format: `.jsonl`

Pflichtfelder:

- `schema_version`
- `session_id`
- `event_id`
- `timestamp`
- `level`
- `code`
- `component`
- `summary`
- `action`
- `details`

### 2. Kurzbericht

Format: `.txt`

Enthält maximal:

- Ampel
- Status
- Fehlercode
- kurze Ursache
- hilfreichen nächsten Schritt
- Session-ID
- Anzahl Warnungen/Fehler

## Dateinamen

Beispiele:

- `maschinenlog_status_laufend_<session>.jsonl`
- `kurzbericht_status_beendet_<session>.txt`
- `kurzbericht_status_absturz_<session>.txt`

## Schweregrade

`DEBUG` · `INFO` · `WARN` · `ERROR` · `CRITICAL`

## Datenschutz

Sensible Schlüssel werden geschwärzt. Echte Nutzerdaten gehören nicht in Debug-Dumps.

## Größenlimits

Die verbindlichen Werte stehen in `MANIFEST.json`. Logs rotieren vor unkontrolliertem Wachstum.
