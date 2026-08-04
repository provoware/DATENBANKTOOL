# DATENBANKTOOL

> Sicheres, portables Linux-Werkzeug zum Suchen, Prüfen und Strukturieren großer chaotischer Datensammlungen – mit Schwerpunkt auf Medien, Audio, Texten, Archiven und Codeprojekten.

## Projektstatus

| Bereich | Stand |
|---|---|
| Version | `0.2.0-alpha.1` |
| Entwicklungsphase | Persistenter Index und Berichte |
| Entwicklungsfortschritt | **36 %** |
| Erledigte Hauptpunkte | **15** |
| Offene Hauptpunkte | **26** |
| SQLite-Schema | **Version 2** |
| Schreibende Dateioperationen | **Noch gesperrt** |
| Standardmodus | **Rein lesend** |

### In dieser Iteration erledigt

1. SQLite-Index mit versioniertem Schema eingeführt.
2. Automatische Migration von Schema V1 auf V2 implementiert und getestet.
3. Transaktionalen Batch-Import mit frei einstellbarer Batchgröße umgesetzt.
4. Wiederaufnahme unterbrochener Scans über persistente Checkpoints umgesetzt.
5. Scan-, Hashing-, Finalisierungs- und Abschlussphasen getrennt gespeichert.
6. Reparaturmodus mit Sicherheitskopie, Integritätsprüfung, `REINDEX`, `ANALYZE` und optionalem `VACUUM` ergänzt.
7. Duplikatgruppen nach Import oder Reparatur reproduzierbar neu aufbaubar gemacht.
8. Gefilterte CSV- und eigenständige HTML-Berichte umgesetzt.
9. Filter für Dateityp, Mindest-/Maximalgröße, Namensprobleme und Duplikatgruppen ergänzt.
10. HTML-Berichte zusätzlich mit lokaler Schnellsuche und interaktiven Filtern ausgestattet.
11. Mehrfachausgaben werden vorab geprüft, damit kein halbes Berichtspaket entsteht.
12. CLI-Kommandos, Dokumentation und Versionsregister erweitert.
13. 14 automatisierte Tests sowie ein vollständiger End-to-End-Probelauf erfolgreich ausgeführt.

### Wichtigste offene Punkte

1. Inkrementelle Aktualisierung bereits abgeschlossener Indexsitzungen.
2. Erkennung gelöschter, verschobener oder geänderter Dateien ohne Vollscan.
3. Fortschrittsereignisse, Pause und kontrollierter Abbruch während Hashing.
4. Volltextsuche und optionaler Inhaltsindex.
5. Grafische, touchfähige Oberfläche für Linux-Desktop und kleine Displays.
6. Vorschaumodule für Bild, Audio, Video, Text, PDF und Archive.
7. Sichere Sortier-, Verschiebe- und Umbenennungspläne mit Voransicht.
8. Transaktionales Undo, Papierkorb, Quarantäne und Wiederherstellung.
9. Paketierung als portables Linux-Programm mit Doppelklick-Start.

### Mögliche nächste Upgrades

- Inkrementeller Re-Scan mit Dateisystem-Fingerabdruck und Änderungsabgleich.
- FTS5-Suchindex für Pfade, Dateinamen und freigegebene Textinhalte.
- PySide6-Oberfläche mit **Einfach**, **Geführt** und **Experte**.
- Fortschritts- und Abbruchkanal für Scan und Hashing.
- FFmpeg/ffprobe- und MediaInfo-Anbindung für echte Medienprüfung.

Weitere Ideen stehen in [`UPGRADE_POOL.md`](UPGRADE_POOL.md).

---

## Sicherheitsgrundsatz

**Analyse zuerst. Änderung später.**

Der aktuelle Stand verändert keine Dateien in den untersuchten Sammlungen. Schreibzugriffe betreffen ausschließlich ausdrücklich gewählte Index- und Berichtsdateien. Vorhandene Berichte werden ohne `--overwrite-report` nicht ersetzt. Der Reparaturmodus legt standardmäßig eine konsistente SQLite-Sicherheitskopie an.

## Aktuell funktionsfähig

### Rein lesender Direkt-Scan

```bash
datenbanktool scan ~/Musik
```

Optionaler JSON-Bericht:

```bash
datenbanktool scan ~/Musik \
  --hash-duplicates \
  --json reports/musik.json
```

### Persistenten SQLite-Index aufbauen

```bash
datenbanktool index build ~/Medien \
  --database index/medien.sqlite3 \
  --batch-size 500 \
  --hash-duplicates
```

Der Import speichert jeden Batch zusammen mit seinem Wiederaufnahme-Checkpoint in einer Transaktion.

### Unterbrochenen Index fortsetzen

```bash
datenbanktool index build ~/Medien \
  --database index/medien.sqlite3 \
  --hash-duplicates \
  --resume
```

Eine Sitzung wird nur fortgesetzt, wenn Wurzelpfad und sicherheitsrelevante Scanoptionen zum gespeicherten Fingerabdruck passen. Andernfalls beginnt eine neue Sitzung.

### Indexstatus anzeigen

```bash
datenbanktool index status index/medien.sqlite3
```

Angezeigt werden Schema-Version, Sitzung, Phase, Status, Dateizahl, Fehler und Duplikatgruppen.

### Index prüfen und reparieren

```bash
datenbanktool index repair index/medien.sqlite3
```

Standardmaßnahmen:

- konsistente SQLite-Sicherheitskopie,
- `PRAGMA quick_check` vor der Reparatur,
- automatische Schemamigration,
- liegengebliebene Sitzungen als unterbrochen markieren,
- Duplikatgruppen neu aufbauen,
- `REINDEX` und `ANALYZE`,
- `PRAGMA integrity_check` und Fremdschlüsselprüfung danach.

Optionale Komprimierung:

```bash
datenbanktool index repair index/medien.sqlite3 --vacuum
```

Die Sicherung lässt sich nur bewusst deaktivieren:

```bash
datenbanktool index repair index/medien.sqlite3 --without-backup
```

### CSV- und HTML-Berichte erzeugen

```bash
datenbanktool report index/medien.sqlite3 \
  --csv reports/medien.csv \
  --html reports/medien.html
```

Filter lassen sich kombinieren:

```bash
datenbanktool report index/medien.sqlite3 \
  --html reports/problematische-audios.html \
  --category audio \
  --min-size-mib 10 \
  --max-size-mib 2000 \
  --name-warning-only \
  --duplicates-only
```

Verfügbare Kategorien:

- `audio`
- `video`
- `image`
- `text`
- `archive`
- `code`
- `document`
- `other`

Der HTML-Bericht ist eine lokale Einzeldatei und bietet zusätzlich:

- Schnellsuche,
- Dateitypfilter,
- Schalter für Namensprobleme,
- Schalter für Duplikate,
- sichtbare Trefferzahl.

## SQLite-Architektur

### Schema-Versionierung

- SQLite `PRAGMA user_version`
- Tabelle `schema_migrations`
- Spiegelung in `metadata.schema_version`
- Abbruch bei Datenbanken, deren Schema neuer als die Programmversion ist

### Zentrale Tabellen

| Tabelle | Zweck |
|---|---|
| `scan_sessions` | Sitzungsstatus, Phase, Checkpoints und Optionen |
| `files` | Dateimetadaten und optionale SHA-256-Werte |
| `filename_warnings` | normalisierte Warncodes pro Datei |
| `scan_errors` | isolierte Datei- und Lesefehler |
| `duplicate_groups` | exakte Duplikatgruppen |
| `duplicate_members` | Zuordnung Dateien zu Duplikatgruppen |
| `schema_migrations` | nachvollziehbare Datenbankmigrationen |

### Wiederaufnahmevertrag

1. Verzeichnislauf ist deterministisch sortiert.
2. Datei-Batch und Checkpoint werden gemeinsam bestätigt.
3. Dateipfade sind je Sitzung eindeutig.
4. Wiederholte Importe aktualisieren statt zu duplizieren.
5. Hashing besitzt einen eigenen Wiederaufnahme-Checkpoint.
6. Erst nach Finalisierung erhält die Sitzung den Status `complete`.

## Projektstruktur

```text
DATENBANKTOOL/
├── src/datenbanktool/
│   ├── cli.py
│   └── core/
│       ├── classification.py
│       ├── index_database.py
│       ├── models.py
│       ├── naming.py
│       ├── reports.py
│       └── scanner.py
├── tests/
│   ├── test_cli.py
│   ├── test_foundation.py
│   └── test_index_database.py
├── project_registry.json
├── ANALYSE-PUNKTE.md
├── SCHWACHSTELLEN.md
├── TODO.md
├── UPGRADE_POOL.md
├── ENTWICKLERDOKU.md
└── CHANGELOG.md
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

## Prüfungen

```bash
python -m compileall -q src tests
PYTHONPATH=src PYTHONWARNINGS=error \
  python -m unittest discover -s tests -v
```

Aktueller validierter Stand:

- **14/14 Tests erfolgreich**
- Python-Kompilierung erfolgreich
- CLI-End-to-End-Test erfolgreich
- Schema-Neuanlage erfolgreich
- V1→V2-Migration erfolgreich
- Unterbrechung und Wiederaufnahme erfolgreich
- Duplikat-Neuaufbau erfolgreich
- Reparatursicherung mit `quick_check = ok`
- gefilterte CSV-/HTML-Ausgabe erfolgreich
- keine Warnungen bei Testausführung mit `PYTHONWARNINGS=error`

Ruff und MyPy waren in der lokalen Prüfungsumgebung nicht installiert und wurden deshalb in dieser Iteration nicht als bestanden ausgewiesen.

## Aktuelle Grenzen

- Wiederaufnahme setzt voraus, dass der gespeicherte Checkpoint im Verzeichnislauf noch auffindbar ist.
- Abgeschlossene Sitzungen werden noch nicht inkrementell aktualisiert.
- Reparatur kann strukturell lesbare Datenbanken korrigieren, aber keine beliebig zerstörte SQLite-Datei garantieren.
- Sehr große HTML-Berichte können den Browser stärker belasten; CSV und SQLite bleiben für große Bestände geeigneter.
- Verschieben, Umbenennen, Editieren, Sortieren und Löschen bleiben gesperrt, bis Plan-, Journal-, Undo- und Recoveryverträge implementiert sind.
