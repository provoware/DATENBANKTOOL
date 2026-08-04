# DATENBANKTOOL

> Sicheres, lokales Linux-Werkzeug zum Suchen, Prüfen und Strukturieren großer chaotischer Datensammlungen – mit Schwerpunkt auf Medien, Audio, Texten, Archiven und Codeprojekten.

## Projektstatus

| Bereich | Stand |
|---|---|
| Version | `0.3.0-alpha.1` |
| SQLite-Schema | `3` |
| Entwicklungsphase | Persistenter inkrementeller Index |
| Entwicklungsfortschritt | **52 %** |
| Erledigte Hauptpunkte | **23** |
| Offene Hauptpunkte | **21** |
| Originaldatei-Schreibzugriffe | **Gesperrt** |
| Standardmodus | **Rein lesend** |

### In dieser Iteration erledigt

1. Inkrementellen Re-Scan entwickelt.
2. Neue, geänderte, verschobene, entfernte und unveränderte Dateien getrennt erfasst.
3. Sichere Linux-Verschiebungserkennung über Geräte-ID, Inode, Größe und Nanosekunden-Zeit entwickelt.
4. Eindeutige Hash-Verschiebungserkennung ergänzt.
5. Hashwerte unveränderter Dateien wiederverwendet.
6. Re-Scan mit persistentem Checkpoint fortsetzbar gemacht.
7. Prozesslock für Vollindex, Re-Scan, Reparatur, Backup und Restore entwickelt.
8. Persistente Fortschrittsereignisse mit Text- und JSONL-Ausgabe entwickelt.
9. `index sessions`, `index backup` und `index restore` ergänzt.
10. Schema-2→3-Migration und 19 Regressionstests ergänzt.

### Wichtigste offene Punkte

1. Schnelle SQLite-Suchschicht mit Pagination und stabiler Sortierung.
2. FTS5-Suche für Namen, Pfade und ausgewählte Textmetadaten.
3. Inkrementelle Ordneraggregate.
4. Sichere Aufbewahrung und Bereinigung alter Sitzungen.
5. Änderungsberichte als JSON, CSV und HTML.
6. Touchfähige PySide6-Oberfläche.
7. Medienvorschau und technische Medienprüfung.
8. Transaktionale Dateiänderungspläne mit Undo und Quarantäne.

Weitere Maßnahmen stehen in [`TODO.md`](TODO.md) und [`UPGRADE_POOL.md`](UPGRADE_POOL.md).

---

## Sicherheitsgrundsatz

**Inventarisieren → vergleichen → erklären → erst später planen und ändern.**

Die aktuelle Alpha-Version verändert keine gescannten Originaldateien. Sie liest Metadaten und Inhalte nur, wenn Hashing ausdrücklich benötigt wird. Löschen, Verschieben, Sortieren und Umbenennen bleiben gesperrt, bis Planmanifest, Konfliktprüfung, Transaktionsjournal, Undo und Recovery vollständig vorhanden sind.

## Kernfunktionen

### Rein lesender Scan

- relative Pfade
- Dateigröße
- Änderungszeit in UTC und Nanosekunden
- Geräte-ID und Inode
- Dateiendung und Kategorie
- Symlink-Status
- große Dateien
- problematische Dateinamen
- optionale SHA-256-Werte
- Einzelfehler ohne Gesamtabsturz

### Persistenter SQLite-Index

- versioniertes Schema
- automatische Migrationen
- WAL-Modus
- Fremdschlüssel
- transaktionale Batches
- sichere Wiederaufnahme
- Reparaturmodus
- frühere Sitzungen bleiben unverändert erhalten

### Inkrementeller Re-Scan

Ein Re-Scan erzeugt einen neuen Snapshot und vergleicht ihn mit einer abgeschlossenen Baseline.

Ergebnisarten:

| Typ | Bedeutung |
|---|---|
| `added` | neue Datei |
| `modified` | Datei am gleichen Pfad wurde geändert oder ersetzt |
| `moved` | eindeutige Verschiebung erkannt |
| `removed` | Datei aus der Baseline fehlt |
| `unchanged` | Identität und relevante Metadaten stimmen überein |

Unsichere Fälle werden nicht erfunden. Eine mehrdeutige mögliche Verschiebung bleibt sichtbar als `added` plus `removed`.

### Prozesslock

Alle schreibenden Indexaktionen verwenden denselben Linux-Prozesslock:

- `index build`
- `index rescan`
- `index repair`
- `index backup`
- `index restore`

Der Lock enthält Diagnoseinformationen zu PID, Host, Zeitpunkt und Operation. Nach Prozessende gibt Linux den Kernel-Lock automatisch frei.

### Fortschrittsereignisse

Indexläufe erzeugen persistente Ereignisse für:

- Start oder Fortsetzung
- bestätigte Batches
- Vergleichsabschluss
- Hashing
- Unterbrechung
- Fehler
- erfolgreichen Abschluss

Ausgabevarianten:

```bash
datenbanktool index rescan ~/Medien --database index.sqlite3 --progress human

datenbanktool index rescan ~/Medien --database index.sqlite3 --progress jsonl

datenbanktool index rescan ~/Medien --database index.sqlite3 --progress quiet
```

## Installation für die Entwicklung

Voraussetzung: Python 3.10 oder neuer.

```bash
git clone https://github.com/provoware/DATENBANKTOOL.git
cd DATENBANKTOOL
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Verwendung

### 1. Vollständige Baseline anlegen

```bash
datenbanktool index build ~/Medien \
  --database index/medien.sqlite3 \
  --batch-size 500 \
  --hash-duplicates
```

### 2. Unterbrochenen Vollindex fortsetzen

```bash
datenbanktool index build ~/Medien \
  --database index/medien.sqlite3 \
  --hash-duplicates \
  --resume
```

### 3. Inkrementellen Re-Scan ausführen

```bash
datenbanktool index rescan ~/Medien \
  --database index/medien.sqlite3
```

Ohne weitere Angaben übernimmt der Re-Scan Hashing-, Symlink- und Größenoptionen aus der Baseline.

### 4. Bestimmte Baseline verwenden

```bash
datenbanktool index rescan ~/Medien \
  --database index/medien.sqlite3 \
  --baseline-session-id 12
```

### 5. Unterbrochenen Re-Scan fortsetzen

```bash
datenbanktool index rescan ~/Medien \
  --database index/medien.sqlite3 \
  --resume
```

### 6. Lock-Wartezeit festlegen

```bash
datenbanktool index rescan ~/Medien \
  --database index/medien.sqlite3 \
  --lock-timeout 15
```

Ohne Wartezeit bricht eine konkurrierende Schreibaktion sofort mit verständlicher Besitzerdiagnose ab.

## Sitzungen verwalten

### Sitzungen auflisten

```bash
datenbanktool index sessions index/medien.sqlite3
```

### Als JSON ausgeben

```bash
datenbanktool index sessions index/medien.sqlite3 --json
```

### Filtern

```bash
datenbanktool index sessions index/medien.sqlite3 \
  --status complete \
  --root ~/Medien \
  --limit 10
```

Die Ausgabe enthält Modus, Status, Baseline, Dateizahl, Fehler, Duplikatgruppen und Änderungszahlen.

## Backup und Restore

### Automatische Sicherung

```bash
datenbanktool index backup index/medien.sqlite3
```

### Festes Ziel

```bash
datenbanktool index backup index/medien.sqlite3 \
  --output backups/medien-2026-08-04.sqlite3
```

Vorhandene Ziele werden nicht still überschrieben. Bewusste Freigabe:

```bash
datenbanktool index backup index/medien.sqlite3 \
  --output backups/medien.sqlite3 \
  --overwrite
```

### Wiederherstellen

```bash
datenbanktool index restore index/medien.sqlite3 \
  --backup backups/medien-2026-08-04.sqlite3
```

Vor der Wiederherstellung wird standardmäßig eine zusätzliche Rückfallsicherung der aktiven Datenbank erzeugt. Nur bewusst deaktivieren:

```bash
datenbanktool index restore index/medien.sqlite3 \
  --backup backups/medien.sqlite3 \
  --without-safety-backup
```

### Sicherheitsablauf beim Restore

1. Sicherungsdatei öffnen.
2. SQLite-Schema prüfen.
3. `PRAGMA quick_check` ausführen.
4. aktive Datenbank optional sichern.
5. Wiederherstellung in temporärer Datenbank aufbauen.
6. temporäre Datenbank erneut prüfen.
7. Ziel atomar ersetzen.
8. Ziel nochmals prüfen.
9. bei Fehler Rückfallsicherung einspielen.

## Status und Reparatur

```bash
datenbanktool index status index/medien.sqlite3

datenbanktool index repair index/medien.sqlite3
```

Optionale Komprimierung:

```bash
datenbanktool index repair index/medien.sqlite3 --vacuum
```

## CSV- und HTML-Berichte

```bash
datenbanktool report index/medien.sqlite3 \
  --csv reports/problemdateien.csv \
  --html reports/problemdateien.html \
  --category audio \
  --min-size-mib 10 \
  --name-warning-only \
  --duplicates-only
```

Filter:

- Dateityp
- Mindestgröße
- Maximalgröße
- Namensprobleme
- Duplikatgruppen
- konkrete Sitzung

HTML-Berichte funktionieren vollständig lokal und enthalten Schnellsuche sowie interaktive Filter.

## Dateinamenprüfung

Linux erlaubt viele Zeichen, die in Shells, Archiven, Netzlaufwerken oder anderen Betriebssystemen problematisch sind. Das Tool meldet unter anderem:

- führende oder abschließende Leerzeichen
- führende Bindestriche
- Steuerzeichen
- Zeilenumbrüche
- schlecht portable Sonderzeichen
- uneinheitliche Unicode-Normalisierung
- überlange Dateinamen
- mehrfach aufeinanderfolgende Leerzeichen

Es wird nichts automatisch umbenannt.

## Projektstruktur

```text
DATENBANKTOOL/
├── src/datenbanktool/
│   ├── cli.py
│   └── core/
│       ├── classification.py
│       ├── incremental.py
│       ├── index_admin.py
│       ├── index_database.py
│       ├── index_lock.py
│       ├── models.py
│       ├── naming.py
│       ├── progress.py
│       ├── reports.py
│       └── scanner.py
├── tests/
├── project_registry.json
├── ANALYSE-PUNKTE.md
├── SCHWACHSTELLEN.md
├── TODO.md
├── UPGRADE_POOL.md
├── ENTWICKLERDOKU.md
└── CHANGELOG.md
```

## Prüfungen

```bash
python -m compileall -q src tests
PYTHONPATH=src PYTHONWARNINGS=error python -m unittest discover -s tests -v
```

Aktueller Prüfstand: **19 von 19 Tests erfolgreich**.

GitHub Actions prüft Python 3.10 und Python 3.12.

## Dokumentation

- [`ANALYSE-PUNKTE.md`](ANALYSE-PUNKTE.md): Änderungsmodell und Architekturentscheidungen
- [`SCHWACHSTELLEN.md`](SCHWACHSTELLEN.md): bekannte Grenzen und Risiken
- [`TODO.md`](TODO.md): priorisierte Umsetzungsschritte
- [`UPGRADE_POOL.md`](UPGRADE_POOL.md): spätere Erweiterungen
- [`ENTWICKLERDOKU.md`](ENTWICKLERDOKU.md): Schema-, Lock-, Backup- und Restoreverträge
- [`CHANGELOG.md`](CHANGELOG.md): Versionshistorie

## Aktuelle Grenze

DATENBANKTOOL ist ein belastbarer, rein lesender Alpha-Datenkern, aber noch kein fertiger Dateimanager. Originaldateien können weiterhin nicht verschoben, gelöscht, sortiert oder umbenannt werden.

## Direkt folgender technischer Entwicklungsschritt

Eine lesende SQLite-Suchschicht mit Pagination, stabiler Sortierung, kombinierbaren Filtern und FTS5 entwickeln.

## Alternative Verbesserung mit hohem Nutzen und geringem Risiko

Änderungen einer Re-Scan-Sitzung über `index changes` als JSON, CSV und HTML sichtbar machen.
