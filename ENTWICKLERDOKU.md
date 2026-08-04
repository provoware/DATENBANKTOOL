# Entwicklerdokumentation

## Architekturstand 0.10.0-alpha.1

Diese Iteration ergänzt zwei getrennte Funktionsbereiche:

1. vollständiger CSV-Export der normalen Ordnerübersicht,
2. reproduzierbare technische Großbestands- und vorbereitete Laienabnahme.

Neue Fachmodule:

- `core/folder_csv.py` – CSV-Schema und atomarer Byte-Schreibvorgang,
- `core/acceptance.py` – Profile, Datensatz, Messung, Kriterien und Berichte,
- `cli_acceptance.py` – Argumente und sichtbare Abnahmeausgabe,
- `tests/test_folder_csv.py` – CSV- und Vollständigkeitstests,
- `tests/test_acceptance.py` – Abnahme- und Sicherheitsprüfungen.

Bestehende Modulgrenzen bleiben erhalten. `cli.py` registriert lediglich den neuen
Parser und enthält keine Abnahmelogik.

## Ordner-CSV

### Öffentlicher Befehl

```text
datenbanktool index folders DATENBANK --csv ZIEL
```

Vollständiger Export:

```text
datenbanktool index folders DATENBANK --csv ZIEL --all-pages
```

`--all-pages` ist nur erlaubt, wenn mindestens eines der Ziele `--json`, `--csv` oder
`--html` gesetzt ist.

### Vollständige Auswertung

`analyse_folders()` besitzt den zusätzlichen Parameter:

```python
all_rows: bool = False
```

Verhalten:

- `False`: bisherige paginierte `FolderPage`,
- `True`: vollständige gefilterte und sortierte Zeilenmenge in einer `FolderPage`.

Die vollständige Auswertung setzt:

- `page=1`,
- `total_pages=1`,
- `page_size=max(1, total_rows)`,
- `rows=tuple(output)`.

Damit bleibt das Datenmodell kompatibel. Es wurde kein zweites paralleles
Exportdatenmodell eingeführt.

### Terminalpagination

`paginate_folder_page()` erzeugt aus einer vollständigen `FolderPage` eine sichtbare
Seite. Vorbedingung:

```text
len(complete_page.rows) == complete_page.total_rows
```

Dadurch wird die teure Ordneraggregation nur einmal ausgeführt. Terminal und Export
verwenden dieselbe sortierte Ergebnismenge.

### CSV-Schema

`export_folder_csv()` schreibt folgende feste Basisspalten:

```text
Ampelstufe
Ampelstatus
Ampelbegründung
Ordner
Ordnertiefe
Dateien direkt
Dateien mit Unterordnern
Größe direkt Byte
Gesamtgröße Byte
Namenshinweise
Dateien in Duplikatgruppen
```

Danach folgen pro vorhandenem `largest_files`-Rang:

```text
Platzfresser N Pfad
Platzfresser N Byte
```

Die maximale Anzahl richtet sich nach der ausgewerteten Seite beziehungsweise bei
`--all-pages` nach der vollständigen Ergebnismenge. Fehlende Werte werden als leere
Zellen geschrieben.

### CSV-Kompatibilität

- Kodierung: `utf-8-sig`,
- Trennzeichen: Semikolon,
- Zeilenende: `\n`,
- numerische Rohwerte: Integer in Byte,
- kein ANSI,
- keine menschenlesbaren Größen in Zahlenfeldern.

### Atomarer Schreibvertrag

`_write_atomic_bytes()`:

1. normalisiert den Zielpfad,
2. lehnt vorhandenes Ziel ohne `overwrite` ab,
3. erstellt notwendige Elternordner,
4. schreibt in eine Prozess-spezifische temporäre Datei,
5. gibt per `replace()` atomar frei,
6. entfernt die temporäre Datei bei Fehlern.

Die gescannte SQLite-Datenbank und Originaldateien bleiben unverändert.

## Abnahmeprofile

`AcceptanceProfile` enthält:

- `name`,
- `file_count`,
- `folder_count`,
- `max_sparse_file_bytes`,
- `max_seconds`,
- `max_python_memory_mib`,
- `description`.

Vordefinierte Profile:

| Profil | Dateien | Ordner | maximale Sparse-Datei | Zeit | Python-Speicher |
|---|---:|---:|---:|---:|---:|
| quick | 600 | 24 | 64 KiB | 30 s | 256 MiB |
| standard | 10.000 | 250 | 512 KiB | 600 s | 1.024 MiB |
| large | 100.000 | 1.000 | 2 MiB | 3.600 s | 4.096 MiB |

Jedes Profil validiert positive Werte.

## Abnahmearbeitsordner

`_safe_workspace()` verlangt einen nicht vorhandenen Zielpfad. Das Modul führt keine
Löschung, Leerung oder Wiederverwendung aus.

Struktur:

```text
WORKSPACE/
├── dataset/
├── index.sqlite3
├── ordneruebersicht.csv
├── acceptance-result.json
├── acceptance-report.md
└── NOVICE_ACCEPTANCE_CHECKLIST.md
```

Bei einem vorhandenen Pfad wird `FileExistsError` ausgelöst, bevor eine Datei verändert
wird.

## Reproduzierbarer Testbestand

`_create_dataset()` verwendet `random.Random(seed)`. Damit bleiben Dateigrößen bei
gleichem Profil und Seed reproduzierbar.

Eigenschaften:

- deterministische Ordnerverteilung,
- gemischte Endungen,
- Leerzeichen,
- Umlaute,
- Fragezeichen und mehrfach gepunktete Namen,
- Dateien werden mit `truncate()` sparse angelegt,
- jede Datei wird exklusiv mit Modus `xb` erzeugt.

Sparse-Dateien prüfen Dateisystem-, Metadaten-, SQLite- und Auswertungsleistung, ohne
den logischen Datenumfang vollständig physisch zu schreiben.

## Quelldaten-Manifest

`_source_manifest()` erfasst für jede Testdatei:

```text
relative_path
st_size
st_mtime_ns
```

Vor und nach Indexaufbau, Ordnerauswertung und CSV-Export werden die Tupel bytegenau
verglichen. Eine Abweichung lässt das Kriterium „Quelldateien unverändert“ scheitern.

Das Manifest verwendet bewusst keine Inhalts-Hashes: Der Indexlauf ohne
Duplikat-Hashing darf Dateiinhalte nicht verändern, und Größe plus Nanosekundenzeit
entdeckt die im Testvertrag relevanten Seiteneffekte mit wesentlich geringerem
Messaufwand.

## Messungen

### Gesamt- und Phasenzeit

`time.perf_counter()` misst:

- Testbestand erzeugen,
- Vorvalidierung,
- Index aufbauen,
- Ordner auswerten,
- CSV exportieren,
- Nachvalidierung,
- Gesamtzeit.

### Python-Spitzenspeicher

`tracemalloc` liefert den Python-Peak in Byte. Dieser Wert besitzt die harte
Profilgrenze.

### Prozess-Maximal-RSS

`resource.getrusage(resource.RUSAGE_SELF).ru_maxrss` wird unter Linux in KiB gelesen
und in Byte umgerechnet. Der Wert wird dokumentiert, besitzt derzeit aber keine harte
profilübergreifende Grenze, weil native Speicherwerte stärker von Plattform und
Bibliotheksbuild abhängen.

## Elf automatische Kriterien

`AcceptanceCheck` enthält Name, Ergebnis, beobachteten Wert, Grenze und Erklärung.

Die Kriterien prüfen:

1. vollständige Erzeugung,
2. Indexstatus `complete`,
3. importierte Dateizahl,
4. null Indexfehler,
5. vorhandene Ordnerauswertung,
6. CSV-Zeilenanzahl,
7. UTF-8-BOM,
8. unverändertes Manifest,
9. CSV- und `all-pages`-Hilfe,
10. Laufzeitgrenze,
11. Python-Speichergrenze.

`result.passed` ist nur wahr, wenn alle Kriterien wahr sind.

## Rückgabecodes

`run_acceptance_command()` liefert:

- `0`, wenn alle automatischen Kriterien bestanden sind,
- `1`, wenn mindestens ein Kriterium verfehlt wird,
- zentrale CLI-Fehlergrenze liefert `2` bei Eingabe-, Pfad-, Datei- oder
  Sicherheitsfehlern.

## Berichte

### JSON

`AcceptanceResult.to_dict()` enthält Profil, Seed, Arbeitsordner, Dateizahlen,
Messwerte, Phasen, Kriterien und Berichtspfade.

### Markdown

Der Bericht enthält:

- Profil und Beschreibung,
- Gesamtergebnis,
- Laufzeit und Speicher,
- Phasen,
- Tabelle aller Kriterien,
- Sicherheitsfazit,
- Hinweis auf offene reale Laienabnahme.

### Laien-Checkliste

Die Checkliste prüft:

- Startseite,
- Ordnerübersicht,
- CSV-Export,
- mehrschichtige Hilfe,
- Sicherheitsverständnis,
- Überschreibfehler,
- Zeit und Irrwege,
- Bewertungen von 1 bis 5,
- klare Bestehensbedingungen.

Der Maschinenstatus bleibt:

```text
pending-real-person
```

Er wird nicht automatisch auf bestanden gesetzt.

## CommandPolicy

Die Abnahme besitzt:

```python
CommandPolicy(
    "acceptance",
    writes_reports=True,
    writes_test_data=True,
)
```

Folgende Werte bleiben falsch:

```text
reads_original_files
writes_original_files
writes_index
```

Der im Arbeitsordner erzeugte Testindex gilt als Teil der isolierten Testdaten, nicht
als Änderung eines Nutzerindexes.

## GitHub Actions

Python 3.10 und 3.12 führen aus:

```text
Installation
compileall
66 Unit-/Integrationstests
```

Python 3.12 führt zusätzlich aus:

```text
quick: 600 Dateien
standard: 10.000 Dateien
```

Für jedes Profil archiviert `actions/upload-artifact@v4`:

- Ergebnis-JSON,
- Markdown-Bericht,
- Laien-Checkliste,
- vollständige Ordner-CSV.

Aufbewahrung: 14 Tage.

## Referenzlauf

Commit `1ebc892d83642d42516da76919cec0c69c036b32`:

| Profil | Kriterien | Laufzeit | Python-Peak | Artefakt-ID |
|---|---:|---:|---:|---:|
| quick | 11/11 | 1,086 s | 1.326.097 Byte | 8895038828 |
| standard | 11/11 | 17,781 s | 13.394.783 Byte | 8895049504 |

Die Werte sind CI-Referenzen und dürfen nicht als plattformunabhängige Zusage behandelt
werden.

## Automatische Tests

`tests/test_folder_csv.py` prüft:

- vollständige Auswertung,
- nachträgliche Pagination,
- UTF-8-BOM,
- Spaltenvertrag,
- Platzfresser,
- Überschreibschutz,
- CLI-Vollständigkeit,
- kontrollierten Fehler ohne Exportziel.

`tests/test_acceptance.py` prüft:

- kleinen reproduzierbaren Lauf,
- vollständige Berichte,
- unveränderte Quellen,
- offenen realen Laienstatus,
- Schutz vorhandener Arbeitsordner,
- Seiteneffektvertrag.

`tests/test_cli_architecture.py` prüft zusätzlich Parser, Handler, Modulzuständigkeit,
Zeilengrenzen und verbotene Shell-Funktionen.

## Bekannte Grenzen

- Reale Laienabnahme noch offen.
- `large`-Profil noch nicht auf Zielhardware ausgeführt.
- Sparse-Dateien simulieren nicht vollständige Medienleselast.
- Harte native RSS-Grenze fehlt noch.
- Ordnervergleich besitzt noch kein `--all-pages`.
- Zeitreihen über mehr als zwei Scans fehlen.

## Direkt folgender Entwicklungsblock

Eine rein lesende Ordner-Zeitreihe über mehrere abgeschlossene Scan-Sitzungen
entwickeln.

## Sichere Alternative

Den Ordnervergleich um einen ausdrücklichen vollständigen Export über `--all-pages`
erweitern.

## Unverändert

`AGENTS.md` wird nicht verändert. Automatische Schreibzugriffe auf gescannte
Originaldateien bleiben gesperrt.
