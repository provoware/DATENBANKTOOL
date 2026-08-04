# Entwicklerdokumentation

## Architekturstand 0.4.0-alpha.1

Der Datenkern besitzt jetzt fünf klar getrennte Bereiche:

1. Scanner für direkte rein lesende Prüfung.
2. Versionierter SQLite-Snapshot-Index.
3. Inkrementeller Re-Scan und Änderungsvergleich.
4. Rein lesende Suchschicht.
5. Berichtsschicht für Dateien und Änderungen.

## Suchschicht

Datei: `src/datenbanktool/core/search.py`

### Sicherheitsvertrag

- Datenbank wird bei normalen Suchabfragen über SQLite-URI `mode=ro` geöffnet.
- `PRAGMA query_only=ON` verhindert versehentliche Schreibabfragen.
- Verbindungen werden mit `contextlib.closing` ausdrücklich geschlossen.
- Alle Filterwerte werden als SQL-Parameter übergeben.
- Seitengröße ist auf 200 begrenzt.
- Jede Sortierung besitzt stabile zusätzliche Sortierfelder.

### Filter

- Suchtext,
- Dateikategorien,
- Mindest- und Maximalgröße,
- Namenswarnungen,
- Duplikatmitgliedschaft,
- konkrete Sitzung.

### Pagination

`LIMIT` und `OFFSET` werden nur aus bereits validierten Ganzzahlen erzeugt. Die Gesamtzahl wird mit einer getrennten `COUNT(*)`-Abfrage bestimmt.

### Stabile Sortierung

Jede Hauptsortierung endet mit:

1. Pfad ohne Beachtung der Groß-/Kleinschreibung,
2. originalem Pfad,
3. eindeutiger Datei-ID.

Damit bleibt die Reihenfolge innerhalb eines unveränderten Snapshots stabil.

## Optionaler FTS5-Index

Der FTS5-Index wird nicht automatisch erzeugt. `build_fulltext_index()` benötigt einen ausdrücklichen Aufruf und verwendet `IndexProcessLock`.

Indizierte Felder:

- `relative_path`,
- `suffix`,
- `category`,
- zusammengefasste Namenswarnungen.

Der Index ist sitzungsbezogen. Die normale Suche prüft zuerst, ob für die gewählte Sitzung FTS-Zeilen vorhanden sind. Ohne FTS5 erfolgt ein sicherer Rückfall auf parameterisierte `LIKE`-Abfragen.

## Änderungsberichte

Datei: `src/datenbanktool/core/changes.py`

### Auswahl

- Standard: neueste abgeschlossene inkrementelle Sitzung.
- Optional: konkrete Sitzungs-ID.
- Nur abgeschlossene Re-Scans mit `parent_session_id` sind zulässig.

### Ausgabe

- Terminal: paginierte, deutsch beschriftete Zeilen.
- JSON: strukturierter Bericht mit Zusammenfassung.
- CSV: UTF-8 mit BOM.
- HTML: eigenständige lokale Datei mit Browserfiltern.

### Dateisicherheit

- Alle Ziele werden vor dem Schreiben geprüft.
- Temporäre Dateien liegen im Zielordner.
- Bei Fehlern werden temporäre Dateien entfernt.
- Bestehende Ziele benötigen `--overwrite-report`.
- HTML-Inhalte werden vollständig maskiert.

## Qualitätsprüfungen

```bash
python -m compileall -q src tests
PYTHONPATH=src PYTHONWARNINGS=error \
  python -m unittest discover -s tests -v
```

Neue Testgruppen prüfen:

- normale Suche ohne Datenbankänderung,
- Pagination und stabile Reihenfolge,
- kombinierte Filter,
- optionalen FTS5-Aufbau,
- FTS5-Suche und Rückfall,
- Änderungszählung,
- Terminalausgabe,
- JSON-/CSV-/HTML-Export,
- Überschreibschutz,
- SQLite-`quick_check`.

## Unverändert

`AGENTS.md` bleibt unverändert. Schreibende Operationen an Originaldateien bleiben blockiert.
