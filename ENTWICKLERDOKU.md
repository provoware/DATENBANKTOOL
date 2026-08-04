# Entwicklerdokumentation

## Architekturstand 0.2.0-alpha.1

DATENBANKTOOL besitzt jetzt drei getrennte Schichten:

1. **Scanner** – rein lesende Direktanalyse.
2. **Indexkern** – persistente, versionierte und wiederaufnehmbare SQLite-Sitzungen.
3. **Berichte** – gefilterte CSV-/HTML-Ausgabe ohne Zugriff auf Nutzerdaten.

Schreibende Dateioperationen bleiben außerhalb dieses Kerns.

## Quellaufbau

- `src/datenbanktool/cli.py`: CLI-Routing und laienverständliche Statusausgabe.
- `src/datenbanktool/core/scanner.py`: Direkt-Scan und gemeinsame SHA-256-Funktion.
- `src/datenbanktool/core/index_database.py`: Schema, Migrationen, Batch-Import, Resume, Status und Reparatur.
- `src/datenbanktool/core/reports.py`: Datenfilter sowie atomare CSV-/HTML-Ausgabe.
- `src/datenbanktool/core/models.py`: neutrale Scanmodelle.
- `project_registry.json`: Projekt-, Versions- und Sicherheitsstatus.

## SQLite-Schema

Aktuelle Version: `2`.

### Migrationsvertrag

- `PRAGMA user_version` ist die technische Schemaquelle.
- `schema_migrations` protokolliert jede angewandte Migration.
- `metadata.schema_version` dient als prüfbarer Spiegel.
- Migrationen laufen einzeln in Transaktionen.
- Neuere, unbekannte Schemaversionen werden abgelehnt.
- Migrationen müssen wiederholbar sicher sein, soweit SQLite dies erlaubt.

### Sitzungsphasen

- `scanning`
- `hashing`
- `finalizing`
- `complete`

### Sitzungsstatus

- `running`
- `interrupted`
- `complete`
- `failed`

Status und Phase sind getrennt: Eine unterbrochene Sitzung kann beispielsweise weiterhin in der Phase `scanning` stehen.

## Batch-Import

Ein Batch enthält:

- Datei-Metadaten,
- normalisierte Namenswarnungen,
- isolierte Scanfehler,
- letzten bearbeiteten relativen Pfad,
- aktualisierte Zähler,
- UTC-Aktualisierungszeit.

Alle Bestandteile werden gemeinsam bestätigt. `UNIQUE(session_id, relative_path)` verhindert doppelte Dateizeilen. Erneutes Einlesen aktualisiert vorhandene Daten.

## Wiederaufnahme

Der Fingerabdruck enthält:

- kanonischen Wurzelpfad,
- Duplikat-Hashing aktiviert/deaktiviert,
- Grenze großer Dateien,
- Symlink-Verhalten.

Batchgröße und `max_files` sind Laufsteuerung und beeinflussen die Kompatibilität nicht.

Der Verzeichnislauf sortiert Verzeichnisse und Dateien deterministisch. Die Wiederaufnahme sucht zunächst den exakten Checkpoint und fährt danach fort. Fehlt der Checkpoint, wird kontrolliert abgebrochen statt unsicher weiterzulaufen.

## Hashing und Duplikate

1. Nur Größenklassen mit mindestens zwei Dateien werden gehasht.
2. Symlinks und leere Dateien werden ausgeschlossen.
3. Hashwerte werden batchweise gespeichert.
4. Duplikatgruppen werden erst in der Finalisierung aus dem Index aufgebaut.
5. Der Reparaturmodus kann Gruppen reproduzierbar neu erzeugen.

## Reparaturvertrag

Standardmäßig wird vor Änderungen mit `sqlite3.Connection.backup()` eine konsistente Sicherungsdatenbank erzeugt. Danach:

1. `quick_check` erfassen.
2. Schema migrieren.
3. `running`-Sitzungen auf `interrupted` setzen.
4. Duplikatgruppen neu aufbauen.
5. `REINDEX` ausführen.
6. `ANALYZE` ausführen.
7. optional `VACUUM` ausführen.
8. `foreign_key_check` und `integrity_check` auswerten.

`successful=True` gilt nur bei `integrity_check = ok` und ohne Fremdschlüsselfehler.

## Berichtsvertrag

- Filter werden in SQL angewandt.
- CSV verwendet UTF-8 mit BOM.
- HTML ist vollständig lokal und eigenständig.
- Dateipfade und Werte werden HTML-escaped.
- vorhandene Ziele werden nicht still ersetzt.
- bei CSV+HTML werden beide Ziele vor dem Schreiben geprüft.
- temporäre Dateien werden bei Fehlern entfernt.

## Qualitätsprüfungen

```bash
python -m compileall -q src tests
PYTHONPATH=src PYTHONWARNINGS=error \
  python -m unittest discover -s tests -v
```

Validierte Fälle:

- Schema-Neuanlage,
- V1→V2-Migration,
- Batchgröße 1,
- Unterbrechung und Wiederaufnahme,
- Eindeutigkeit importierter Pfade,
- Duplikatgruppen nach Wiederaufnahme,
- Indexstatus,
- Reparatursicherung und Integrität,
- kombinierte Berichtfilter,
- Überschreibschutz,
- Schutz vor halbem Mehrfachbericht,
- CLI-End-to-End-Ablauf.

Zusätzlich läuft GitHub Actions unter Python 3.10 und 3.12 mit `compileall`, vollständigen Unittests und `PYTHONWARNINGS=error`.

## Nächster Architekturblock

Inkrementeller Re-Scan mit Änderungsabgleich, Prozesslock und Fortschrittsereignissen. Erst danach sollte die grafische Oberfläche auf dem Indexkern aufsetzen.

## Unverändert

`AGENTS.md` bleibt unverändert.
