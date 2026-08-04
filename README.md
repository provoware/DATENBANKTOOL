# DATENBANKTOOL

> Ein sicheres Linux-Werkzeug zum Finden, Prüfen und Ordnen großer chaotischer Dateisammlungen.

## Projektstatus

| Bereich | Stand |
|---|---|
| Version | `0.4.0-alpha.1` |
| SQLite-Schema | `3` |
| Entwicklungsfortschritt | **66 %** |
| Erledigte Hauptpunkte | **29** |
| Offene Hauptpunkte | **15** |
| Originaldateien verändern | **Nein** |
| Standardmodus | **Rein lesend** |

### Neu in dieser Version

1. Dateien direkt im gespeicherten Index suchen.
2. Lange Trefferlisten in überschaubare Seiten teilen.
3. Ergebnisse sicher und immer gleich sortieren.
4. Filter für Dateityp, Größe, Namensprobleme und Duplikate kombinieren.
5. Optional einen schnelleren FTS5-Suchindex für Dateinamen und Pfade aufbauen.
6. Änderungen eines Re-Scans im Terminal sowie als JSON, CSV und HTML ausgeben.

## Wichtigster Sicherheitsgrundsatz

**Suchen und Berichte verändern keine Originaldateien.**

Die normale Suche öffnet die SQLite-Datenbank nur zum Lesen. Der optionale schnelle Suchindex wird ausschließlich mit dem ausdrücklichen Schalter `--build-fulltext-index` erzeugt. Auch dabei werden keine Medien, Texte oder anderen Originaldateien verändert.

## Einfache Suche

```bash
datenbanktool index search index.sqlite3 urlaub
```

Das Tool durchsucht den neuesten abgeschlossenen Scan und zeigt:

- Dateipfad,
- Dateityp,
- Größe,
- Namensprobleme,
- Duplikatstatus.

### Seitenweise anzeigen

```bash
datenbanktool index search index.sqlite3 musik --page 2 --page-size 25
```

Am Ende jeder Seite wird der Befehl für die nächste Seite angezeigt.

### Nach Dateityp filtern

```bash
datenbanktool index search index.sqlite3 live \
  --category audio \
  --category video
```

### Nach Größe filtern

```bash
datenbanktool index search index.sqlite3 \
  --min-size-mib 100 \
  --max-size-mib 2000 \
  --sort size \
  --descending
```

### Nur problematische Dateinamen

```bash
datenbanktool index search index.sqlite3 --name-warning-only
```

### Nur erkannte Duplikate

```bash
datenbanktool index search index.sqlite3 --duplicates-only
```

### JSON-Ausgabe für andere Programme

```bash
datenbanktool index search index.sqlite3 track --json
```

## Optionaler schneller Suchindex

Die normale Suche funktioniert immer. Bei sehr großen Sammlungen kann zusätzlich ein schneller FTS5-Index für Dateinamen, Pfade, Endungen, Dateitypen und Namenswarnungen aufgebaut werden:

```bash
datenbanktool index search index.sqlite3 \
  --build-fulltext-index
```

Danach wird er automatisch verwendet:

```bash
datenbanktool index search index.sqlite3 techno
```

FTS5 kann ausdrücklich verlangt werden:

```bash
datenbanktool index search index.sqlite3 techno --fulltext required
```

Ist FTS5 in der verwendeten Python-/SQLite-Installation nicht vorhanden, bleibt die normale Suche vollständig nutzbar.

## Änderungen seit dem vorherigen Scan

### Verständliche Terminalansicht

```bash
datenbanktool index changes index.sqlite3
```

Die Ausgabe unterscheidet:

- **Neu** – Datei ist hinzugekommen.
- **Geändert** – Dateiinhalt oder Dateidaten haben sich geändert.
- **Verschoben** – Datei wurde eindeutig an einem anderen Ort erkannt.
- **Entfernt** – Datei ist im neuen Scan nicht mehr vorhanden.
- **Unverändert** – Datei ist gleich geblieben.

### Nur bestimmte Änderungen anzeigen

```bash
datenbanktool index changes index.sqlite3 \
  --type moved \
  --type modified
```

### Nach Dateityp oder Pfad filtern

```bash
datenbanktool index changes index.sqlite3 \
  --category audio \
  --contains live
```

### Berichte gleichzeitig erzeugen

```bash
datenbanktool index changes index.sqlite3 \
  --json reports/aenderungen.json \
  --csv reports/aenderungen.csv \
  --html reports/aenderungen.html
```

Die HTML-Datei funktioniert vollständig lokal und besitzt eigene Such- und Filterfelder.

Vorhandene Berichte werden nicht still überschrieben. Dafür ist eine ausdrückliche Freigabe nötig:

```bash
datenbanktool index changes index.sqlite3 \
  --html reports/aenderungen.html \
  --overwrite-report
```

## Weitere wichtige Befehle

```bash
# Ersten Index aufbauen
datenbanktool index build ~/Medien --database index.sqlite3

# Änderungen seit dem letzten Scan erkennen
datenbanktool index rescan ~/Medien --database index.sqlite3

# Gespeicherte Scans anzeigen
datenbanktool index sessions index.sqlite3

# Index sichern
datenbanktool index backup index.sqlite3

# Sicherung wiederherstellen
datenbanktool index restore index.sqlite3 --backup sicherung.sqlite3

# Index prüfen und reparieren
datenbanktool index repair index.sqlite3
```

## Suchregeln

- Ohne Sitzungsnummer wird der neueste abgeschlossene Scan verwendet.
- Seiten beginnen bei `1`.
- Pro Seite sind höchstens `200` Treffer erlaubt.
- Jede Sortierung besitzt zusätzliche feste Vergleichsfelder. Dadurch springt die Reihenfolge nicht zufällig.
- Die Suche arbeitet immer innerhalb eines gespeicherten Snapshots.
- Mehrere Filter werden gemeinsam angewandt.

## Projektstruktur

```text
src/datenbanktool/
├── cli.py
└── core/
    ├── search.py          # rein lesende Suche und optionaler FTS5-Aufbau
    ├── changes.py         # Änderungsansicht und Export
    ├── incremental.py     # Re-Scan und Änderungsvergleich
    ├── index_admin.py     # Sitzungen, Backup und Restore
    ├── index_schema.py    # SQLite-Migrationen
    └── reports.py         # allgemeine Dateiberichte
```

## Prüfungen

```bash
python -m compileall -q src tests
PYTHONPATH=src PYTHONWARNINGS=error \
  python -m unittest discover -s tests -v
```

GitHub Actions prüft das Projekt zusätzlich mit Python 3.10 und Python 3.12.

## Noch nicht freigegeben

- Dateien automatisch verschieben,
- Dateien automatisch umbenennen,
- Dateien löschen,
- ähnliche Bilder oder Audios automatisch bewerten,
- grafische Oberfläche.

Diese Funktionen bleiben gesperrt, bis Vorschau, Konfliktprüfung, Undo und Wiederherstellung vollständig vorhanden sind.
