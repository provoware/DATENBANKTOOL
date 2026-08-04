# Entwicklerdokumentation

## Architekturstand 0.11.0-alpha.1

Diese Iteration ergänzt zwei getrennte Funktionen:

1. rein lesende Ordner-Zeitreihe über mehrere abgeschlossene Scans,
2. vollständiger Export aller gefilterten Ordnervergleichszeilen.

Neue Fachmodule:

- `core/folder_timeline.py` – Pfadprüfung, Sitzungsauswahl, Messwerte und Zustände,
- `core/folder_timeline_exports.py` – atomare JSON-, CSV- und HTML-Berichte,
- `cli_folder_timeline.py` – Parser, Terminaldarstellung und Dispatch,
- `tests/test_folder_timeline_and_compare_exports.py` – Funktions-, Sicherheits-
  und Vollständigkeitstests.

Bestehende Vergleichsmodule wurden gezielt erweitert:

- `core/folder_compare.py` – vollständige Ergebnismenge und nachträgliche Pagination,
- `cli_folder_compare.py` – sichtbarer `--all-pages`-Schalter.

`cli.py` registriert nur das neue Fachmodul und bleibt unter dem globalen Limit.

## Öffentlicher Zeitreihenbefehl

```text
datenbanktool index folder-timeline DATENBANK [ORDNER]
```

Optionen:

```text
--from-session-id ID
--to-session-id ID
--limit 2..500
--json PFAD
--csv PFAD
--html PFAD
--overwrite-report
--no-terminal
```

Ohne `ORDNER` wird `.` verwendet. Dieser Wert steht für den gesamten gespeicherten
Stammordner.

## Datenmodelle

### `FolderTimelineOptions`

Enthält:

- `folder`: relativer Ordnerpfad,
- `from_session_id`: optional älteste Sitzung,
- `to_session_id`: optional neueste Sitzung,
- `limit`: höchstens anzuzeigende neueste Zeitpunkte.

Validierung:

- Sitzungs-IDs mindestens 1,
- Limit zwischen 2 und 500,
- sicherer relativer Ordnerpfad.

### `FolderTimelinePoint`

Ein Zeitpunkt enthält:

- `session_id`,
- `recorded_utc`,
- `scan_mode`,
- `file_count`,
- `size_bytes`,
- `file_delta`,
- `size_delta_bytes`,
- `size_delta_percent`,
- technischen und sichtbaren Status,
- Ampelstufe, Status und Begründung.

Der erste sichtbare Zeitpunkt besitzt keine Differenz und wird als `baseline`
klassifiziert.

### `FolderTimeline`

Die gesamte Zeitreihe enthält:

- normalisierten Datenbankpfad,
- Stammordner,
- relativen Zielordner,
- Zahl aller verfügbaren Sitzungen,
- Kürzungsstatus,
- erste und letzte Scan-ID,
- Nettoänderung von Dateien und Größe,
- minimale und maximale Größe,
- unveränderliche Punktfolge.

## Sichere Pfadnormalisierung

`normalise_folder()`:

1. entfernt äußere Leerzeichen,
2. wandelt Backslashes in `/` um,
3. behandelt leer, `.`, `./` als Stammordner,
4. lehnt absolute Pfade ab,
5. lehnt jedes Segment `..` ab,
6. speichert einen kanonischen relativen POSIX-Pfad.

Dadurch kann eine Nutzereingabe nicht aus dem gespeicherten Stammordner herauszeigen.

## Rein lesender SQLite-Vertrag

`_readonly_connection()`:

1. normalisiert den Datenbankpfad,
2. verlangt eine vorhandene Datei,
3. öffnet SQLite als URI mit `mode=ro`,
4. aktiviert `PRAGMA query_only=ON`,
5. lehnt neuere unbekannte Schemata ab,
6. verlangt Schema 3 für Scan-Beziehungen und Scan-Modus.

Die Zeitreihe führt keine schreibenden SQL-Anweisungen aus und startet keinen neuen
Dateisystemscan.

## Sitzungsauswahl

### Zielsitzung

- Mit `--to-session-id` wird genau diese abgeschlossene Sitzung verwendet.
- Ohne Angabe wird die neueste abgeschlossene Sitzung gewählt.

### Ausgangssitzung

- Mit `--from-session-id` wird eine untere inklusive Grenze gesetzt.
- Sie darf nicht neuer als die Zielsitzung sein.
- Ihr normalisierter Stammordner muss mit der Zielsitzung übereinstimmen.

### Auswahlmenge

Alle abgeschlossenen Sitzungen mit gleichem Stammordner und passender ID-Spanne werden
chronologisch ausgewählt. Liegen mehr als `limit` Sitzungen vor, werden die neuesten
Zeitpunkte verwendet und `truncated=True` gesetzt.

Weniger als zwei ausgewählte Sitzungen führen zu einem kontrollierten Fehler.

## Rekursive Ordneraggregation

Für den Stammordner `.` wird pro Sitzung berechnet:

```sql
COUNT(*)
SUM(size_bytes)
```

Für einen Unterordner wie `Musik/Live` wird ein Präfix mit abschließendem `/` verwendet:

```text
Musik/Live/
```

Die SQL-Bedingung vergleicht genau diesen Präfix. Dadurch zählt `Musik/Live2` nicht
versehentlich mit.

Die Auswertung verwendet ausschließlich bereits gespeicherte `files`-Zeilen.

## Zustandslogik

Für jeden Punkt nach dem Ausgangswert gilt folgende Reihenfolge:

1. vorher 0 Dateien, jetzt mehr als 0 → `new`,
2. vorher Dateien, jetzt 0 → `removed`,
3. Größe gestiegen → `grown`,
4. Größe gesunken → `shrunk`,
5. Größe gleich, Dateizahl anders → `changed`,
6. sonst → `unchanged`.

Prozentwert:

```text
(size_delta / previous_size) * 100
```

Bei einem Ausgangswert von 0 bleibt der Prozentwert `None`; es wird kein künstlicher
unendlicher Wert erzeugt.

## Darstellung

`cli_folder_timeline.py` zeigt:

- Stammordner und relativen Ordner,
- Scan-Spanne und Punktzahl,
- transparente Kürzungsinformation,
- Nettoänderung,
- Minimum und Maximum,
- jeden Punkt mit Ampel, Zeit, Modus, Dateien, Größe und Differenzen.

Farben sind nur Zusatzinformation. Klartext und Begründung bleiben immer sichtbar.

## Zeitreihenexporte

### JSON

- UTF-8,
- eingerückt,
- vollständige Metadaten und Punkte,
- keine ANSI-Farben oder Bedienhinweise.

### CSV

- UTF-8 mit BOM,
- Semikolon,
- numerische Rohwerte in Byte,
- getrennte Status- und Begründungsspalten,
- Ordner und Stammordner pro Zeile für eigenständige Weiterverarbeitung.

### HTML

- vollständig offline,
- dynamische Texte HTML-maskiert,
- sichtbare Tabelle,
- Tooltip und `aria-label`,
- Kürzungsinformation und Sicherheitshinweis,
- keine externen Skripte, Fonts oder Stylesheets.

### Atomarer Schreibvorgang

Alle Formate werden zuerst in eine Prozess-spezifische temporäre Datei geschrieben und
anschließend per `replace()` freigegeben. Bei Fehlern wird die temporäre Datei entfernt.
Vorhandene Ziele benötigen `overwrite=True`.

## Vollständiger Ordnervergleichsexport

### Core-Erweiterung

`compare_folders()` besitzt jetzt:

```python
all_rows: bool = False
```

- `False`: bisherige paginierte Seite,
- `True`: vollständige gefilterte und sortierte Ergebnismenge.

Die vollständige Seite verwendet:

```text
page = 1
page_size = max(1, total_rows)
total_pages = 1
rows = tuple(output)
```

### Terminalpagination

`paginate_folder_comparison()` verlangt eine vollständige Seite und erzeugt daraus die
sichtbare Terminalseite. Dadurch wird die aufwendige Aggregation beider Snapshots nur
einmal ausgeführt.

### CLI-Steuerung

`--all-pages`:

- ist nur mit mindestens einem Exportziel zulässig,
- hält das Terminal paginiert,
- übergibt die vollständige Seite an JSON, CSV und HTML,
- verändert das Verhalten ohne Schalter nicht.

## CommandPolicy

Zeitreihe:

```python
CommandPolicy("index.folder-timeline", writes_reports=True)
```

Vergleich:

```python
CommandPolicy("index.folder-compare", writes_reports=True)
```

Für beide bleiben falsch:

```text
writes_original_files
writes_index
writes_backups
writes_configuration
writes_test_data
```

## Automatische Tests

`tests/test_folder_timeline_and_compare_exports.py` prüft:

1. drei chronologische Scans,
2. rekursive Dateien und Größen,
3. Wachstum und Rückgang,
4. Nettoänderung,
5. bytegenau unveränderte Datenbank,
6. JSON-, CSV- und HTML-Ausgabe,
7. UTF-8-BOM,
8. direkten CLI-Befehl,
9. Ablehnung von `../`,
10. Mindestanzahl von zwei Scans,
11. vollständigen Vergleichsexport über mehrere Seiten,
12. identische Zeilenzahl in JSON, CSV und HTML,
13. kontrollierten Fehler bei `--all-pages` ohne Exportziel.

`tests/test_cli_architecture.py` prüft zusätzlich:

- registrierten Handler,
- vorhandene und gültige `CommandPolicy`,
- Zuständigkeit von `cli_folder_timeline.py`,
- CLI-Zeilengrenzen,
- Importgrenzen und Shell-Verbote.

Gesamtstand:

- 71 Tests unter Python 3.10,
- 71 Tests unter Python 3.12,
- Warnungen als Fehler,
- vollständige Kompilierung von `src` und `tests`.

## Bekannte Grenzen

- Noch kein eigener Startseitenpunkt für die Zeitreihe.
- Noch keine mehrschichtige Feld- und Fehlerhilfe in der Startseite.
- HTML besitzt noch keine SVG-Liniengrafik.
- Zeitreihe zeigt jeweils einen relativen Ordner.
- Leere Ordner ohne Dateieintrag bleiben unsichtbar.
- Reale Laienabnahme und 100.000-Dateien-Zieltest bleiben offen.

## Direkt folgender Entwicklungsblock

Zeitreihe in die geführte Startseite und das mehrschichtige Hilfesystem integrieren.

## Sichere Alternative

Zwei barrierefreie lokale SVG-Liniengrafiken für Größe und Dateizahl im HTML-Bericht
ergänzen.

## Unverändert

`AGENTS.md` wird nicht verändert. Externe Laufzeitabhängigkeiten bleiben bei null, und
automatische Schreibzugriffe auf gescannte Originaldateien bleiben gesperrt.
