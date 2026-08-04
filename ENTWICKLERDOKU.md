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

Enthält relativen Ordnerpfad, optionale Ausgangs- und Zielsitzung sowie das Limit.
Sitzungs-IDs müssen mindestens 1 und das Limit zwischen 2 und 500 liegen.

### `FolderTimelinePoint`

Ein Zeitpunkt enthält Scan-ID, UTC-Zeit, Scan-Modus, Dateizahl, Größe, Differenzen,
Prozentwert, Status sowie Ampelmetadaten. Der erste sichtbare Punkt ist `baseline` und
besitzt keine Differenz.

### `FolderTimeline`

Die gesamte Zeitreihe enthält Datenbank, Stammordner, relativen Ordner, verfügbare und
sichtbare Sitzungen, Kürzungsstatus, Nettoänderungen, Minimum, Maximum und Punkte.

## Sichere Pfadnormalisierung

`normalise_folder()`:

1. entfernt äußere Leerzeichen,
2. wandelt Backslashes in `/` um,
3. behandelt leer, `.`, `./` als Stammordner,
4. lehnt absolute Pfade ab,
5. lehnt jedes Segment `..` ab,
6. liefert einen kanonischen relativen POSIX-Pfad.

## Rein lesender SQLite-Vertrag

`_readonly_connection()`:

1. normalisiert den Datenbankpfad,
2. verlangt eine vorhandene Datei,
3. öffnet SQLite mit `mode=ro`,
4. aktiviert `PRAGMA query_only=ON`,
5. lehnt unbekannte neuere Schemata ab,
6. verlangt Schema 3.

Die Zeitreihe führt keine schreibende SQL-Anweisung und keinen neuen Dateisystemscan
aus.

## Sitzungsauswahl

- `--to-session-id` wählt eine konkrete abgeschlossene Zielsitzung.
- Ohne Ziel wird die neueste abgeschlossene Sitzung gewählt.
- `--from-session-id` setzt eine inklusive untere Grenze.
- Ausgang und Ziel müssen denselben normalisierten Stammordner besitzen.
- Alle passenden Sitzungen werden chronologisch sortiert.
- Bei mehr Punkten als `limit` werden die neuesten verwendet und die Kürzung gemeldet.
- Weniger als zwei Punkte führen zu einem kontrollierten Fehler.

## Rekursive Ordneraggregation

Für `.` werden alle Dateizeilen einer Sitzung gezählt und summiert. Für Unterordner
wird ein Präfix mit abschließendem `/` verwendet. Dadurch zählt `Musik/` die Dateien
in `Musik/Live/`, aber nicht versehentlich `Musik-Alt/`.

## Zustandslogik

1. vorher 0 Dateien, jetzt mehr als 0 → `new`,
2. vorher Dateien, jetzt 0 → `removed`,
3. Größe gestiegen → `grown`,
4. Größe gesunken → `shrunk`,
5. Größe gleich, Dateizahl anders → `changed`,
6. sonst → `unchanged`.

Bei vorheriger Größe 0 bleibt der Prozentwert `None`.

## Zeitreihenexporte

### JSON

UTF-8, eingerückt, vollständige Metadaten und keine ANSI-Ausgaben.

### CSV

UTF-8-BOM, Semikolon, numerische Rohwerte, getrennte Status- und Begründungsspalten.

### HTML

Vollständig offline, HTML-maskiert, sichtbare Tabelle, Tooltip und `aria-label`.

### Atomarer Schreibvertrag

Alle Formate werden in eine Prozess-spezifische temporäre Datei geschrieben und per
`replace()` freigegeben. Vorhandene Ziele benötigen `overwrite=True`.

## Vollständiger Ordnervergleichsexport

`compare_folders()` besitzt jetzt `all_rows: bool = False`.

- `False`: bisherige paginierte Seite,
- `True`: vollständige gefilterte und sortierte Ergebnismenge.

`paginate_folder_comparison()` erzeugt aus der vollständigen Menge die sichtbare
Terminalseite. Die Aggregation beider Snapshots erfolgt nur einmal.

`--all-pages` ist nur mit JSON, CSV oder HTML zulässig. Ohne Schalter bleibt das
bisherige Seitenverhalten kompatibel.

## CommandPolicy

```python
CommandPolicy("index.folder-timeline", writes_reports=True)
CommandPolicy("index.folder-compare", writes_reports=True)
```

Originaldatei-, Index-, Backup-, Konfigurations- und Testdatenschreibzugriffe bleiben
für beide Befehle falsch.

## Automatische Tests

Die neue Testdatei prüft:

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

Der Architekturtest prüft Handler, `CommandPolicy`, Modulzuständigkeit, Zeilengrenzen,
Importgrenzen und Shell-Verbote.

## Finale Validierung

Referenzcommit `900efee174464413e3b8216924081248294787c6`:

- Paket `datenbanktool-0.11.0a1` gebaut,
- 71/71 Tests unter Python 3.10,
- 71/71 Tests unter Python 3.12,
- Warnungen als Fehler,
- Quick: 600 Dateien, 11/11, 1,131 s, 1.327.056 Byte Python-Peak,
- Standard: 10.000 Dateien, 11/11, 18,072 s, 13.396.733 Byte Python-Peak,
- getrennte Artefakte mit SHA-256-Prüfsummen.

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
