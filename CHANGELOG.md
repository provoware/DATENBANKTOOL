# Changelog

## 0.4.0-alpha.1 – 2026-08-04

### Hinzugefügt

- Rein lesende SQLite-Suche über gespeicherte Scan-Sitzungen.
- Seitenweise Trefferanzeige mit frei wählbarer Seitengröße bis 200.
- Stabile Sortierung nach Pfad, Größe, Datum und Dateityp.
- Kombinierbare Filter für Suchtext, Dateityp, Größe, Namensprobleme und Duplikate.
- JSON-Ausgabe der Suchergebnisse.
- Optionaler FTS5-Index für Dateinamen, Pfade, Endungen, Typen und Namenswarnungen.
- `index changes` mit verständlicher Terminalansicht.
- Änderungsberichte als JSON, CSV mit UTF-8-BOM und lokale HTML-Datei.
- Filter für Änderungsart, Dateityp und Pfadtext.
- Interaktive Suche und Filter im HTML-Änderungsbericht.
- Neue Integrations- und Sicherheitstests.

### Sicherheitsverbesserungen

- Normale Suchabfragen öffnen SQLite mit `mode=ro` und `query_only`.
- SQLite-Verbindungen werden ausdrücklich geschlossen.
- FTS5-Aufbau benötigt einen bewussten Schalter und verwendet den Prozesslock.
- Mehrere Berichtziele werden vollständig vor dem Schreiben geprüft.
- Vorhandene Ausgabedateien werden nicht still überschrieben.
- Alle HTML-Werte werden maskiert.

### Unverändert

- Originaldateien werden nicht verändert.
- Schreibende Dateioperationen bleiben gesperrt.
- `AGENTS.md` bleibt unverändert.

## 0.3.0-alpha.1 – 2026-08-04

- Inkrementeller Re-Scan, Prozesslock, Fortschrittsereignisse, Sitzungsverwaltung, Backup und Restore.

## 0.2.0-alpha.1 – 2026-08-04

- Persistenter SQLite-Index, Migration, Batch-Import, Wiederaufnahme, Reparatur sowie CSV-/HTML-Dateiberichte.

## 0.1.0-alpha.1 – 2026-08-04

- Rein lesender Scanner, Dateiklassifizierung, Namensprüfung und exakte Duplikaterkennung.
