# Entwicklerdokumentation

## Architekturstand `0.15.0-alpha.1` / `0.15.0a1`

Diese Iteration ergänzt einen begrenzten, überprüfbaren Wiederanlaufvertrag. Sie verspricht keine Unabhängigkeit von defekter Hardware, verhindert aber innerhalb des Anwendungs- und Dateisystemvertrags halb veröffentlichte Dateien, unklare Prozessenden und verlorene bestätigte Scanbatches.

## Neue Fachmodule

| Modul | Verantwortung |
|---|---|
| `core/durable_files.py` | dauerhafte atomare Veröffentlichung von Dateien |
| `core/run_journal.py` | Laufstatus, Crashberichte und Argument-Ausblendung |
| `core/diagnostics.py` | Start-, Schreib-, Laufjournal- und Nur-Lese-Indexdiagnose |
| `cli_check.py` | verständlicher öffentlicher Befehl `datenbanktool check` |
| `tests/test_crash_safety.py` | Ausfall-, Abbruch-, Wiederaufnahme- und Sprachtests |

## Prozessgrenze

Der installierte Konsolenbefehl endet in `entrypoint.main()`. `_run_safely()` umschließt Hilfe, Startseite und normale CLI-Ausführung.

| Zustand | Rückgabecode | Laufjournal |
|---|---:|---|
| Erfolg | `0` | `complete` |
| kontrollierter Bedien-/Datenfehler | `1` oder `2` | `controlled-error` |
| unerwartete Ausnahme | `70` | `failed` plus Crashbericht |
| Tastaturabbruch | `130` | `interrupted` |

`SystemExit` aus argparse bleibt argparse-kompatibel, schließt das Journal jedoch kontrolliert. Unerwartete Ausnahmen werden nicht in der inneren CLI als Bedienfehler maskiert.

## Laufjournal und Crashbericht

Standardordner:

```text
$XDG_STATE_HOME/datenbanktool/
```

Fallback:

```text
~/.local/state/datenbanktool/
```

`last-run.json` enthält Schema, Status, Zeiten, Exitcode, Version, Python, Plattform, Prozess-ID und bereinigte Argumente. Crashberichte besitzen einen eindeutigen Zeit-/PID-Namen und zusätzlich Traceback und Python-Executable.

Argumente hinter Schaltern mit `token`, `password`, `passwort`, `secret`, `apikey` oder `api-key` werden durch `<ausgeblendet>` ersetzt. Dies ist eine Mindestbarriere, kein allgemeiner Geheimnisscanner.

## Dauerhafte Dateifreigabe

`atomic_write_bytes()` und `atomic_write_text()` verwenden:

1. `mkstemp()` im Zielordner,
2. vollständiges Schreiben,
3. `flush()` und Datei-`fsync`,
4. optionalen Dateimodus,
5. erneute Überschreibprüfung,
6. `os.replace()` im selben Dateisystem,
7. Verzeichnis-`fsync`,
8. Temp-Bereinigung bei jedem `BaseException`.

`publish_temp_file()` veröffentlicht bereits vorbereitete Dateien, beispielsweise geprüfte SQLite-Sicherungen. Ein fehlgeschlagenes `replace` lässt die alte Zieldatei bestehen.

## SQLite-Vertrag

Schreibende `IndexDatabase`-Verbindungen setzen:

```sql
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;
PRAGMA wal_autocheckpoint = 1000;
```

`durable_checkpoint()` bestätigt zuerst die Transaktion. Danach wird ein passiver WAL-Checkpoint versucht. `busy` oder `locked` bedeutet nur, dass die WAL-Aufräumphase später stattfindet; der Commit bleibt gültig. Andere SQLite-Fehler werden weitergegeben.

Abschluss, Unterbrechung und Fehlerstatus werden jeweils committed. `close()` darf einen bereits laufenden fachlichen Fehler nicht durch einen sekundären Close-Fehler verdecken.

## Autosave

`IndexBuildOptions` und `IncrementalScanOptions` besitzen:

```python
batch_size: int = 500
autosave_seconds: float = 5.0
```

Ein Batch wird bestätigt, sobald eine Bedingung erfüllt ist:

```text
Anzahl gepufferter Datensätze >= batch_size
ODER
monotonic() - last_save >= autosave_seconds
```

Dies gilt für Metadatenscan und Prüfsummenphase. Nach jedem Autosave wird ein Fortschrittsereignis gespeichert.

### Wiederaufnahme

- `last_relative_path` setzt den Dateiscan fort.
- `last_hash_path` setzt die Prüfsummenphase fort.
- Fingerprint und Scanart müssen zum unterbrochenen Lauf passen.
- Der Checkpoint muss weiterhin im Ordner vorkommen; andernfalls wird ein kontrollierter `ResumeCheckpointError` ausgelöst.
- Ein Hash kann nicht innerhalb einer einzelnen Datei fortgesetzt werden. Nur diese Datei wird nach Absturz erneut gehasht.

## Sicherung und Wiederherstellung

Sicherung:

1. SQLite-Backup-API in eine neue Temp-Datenbank,
2. Zielverbindung schließen,
3. `quick_check`,
4. Datei-`fsync`, atomare Veröffentlichung und Ordner-`fsync`.

Wiederherstellung:

1. Eingangssicherung validieren,
2. standardmäßig Rückfallsicherung des aktiven Index,
3. Backup-API in Temp-Ziel,
4. Temp-Ziel validieren,
5. aktiven WAL abschließen,
6. dauerhafte atomare Veröffentlichung,
7. Ziel erneut validieren,
8. bei Fehler Rückfallsicherung verwenden.

## Startklar-Prüfung

`datenbanktool check` prüft:

- Python-Mindestversion,
- SQLite-Verfügbarkeit,
- dauerhaften Schreibtest im eigenen Konfigurationsordner,
- dauerhaften Schreibtest im Statusordner,
- Hinweis auf früheren unvollständigen Lauf,
- optional Indexexistenz, Nur-Lese-Öffnung, Schema und `quick_check`.

Die Diagnose verändert keine Originaldateien. Die beiden Schreibtests erzeugen nur kurzlebige Dateien in den eigenen Toolordnern.

## Nutzeransprache

Neue zentrale Texte folgen diesem Vertrag:

1. verständliche Aussage,
2. Auswirkung auf persönliche Dateien,
3. konkrete nächste Handlung,
4. technische Einzelheit danach.

Technische Begriffe werden nicht entfernt, sondern nachgeordnet. Maschinenlesbare JSON-Ausgaben bleiben sachlich und frei von ANSI-Sequenzen.

## Automatische Prüfungen

`tests/test_crash_safety.py` simuliert:

- vorhandenes Ziel ohne Überschreibfreigabe,
- fehlgeschlagenes `os.replace`,
- Modus `0600`,
- Crashbericht und Geheimnis-Ausblendung,
- Tastaturabbruch,
- kontrollierte Scanunterbrechung und `--resume`,
- `synchronous=FULL`,
- unveränderte Indexdatei durch Diagnose,
- Parser- und Policy-Anbindung,
- Alltagssprache vor technischem Detail.

`tests/test_cli_architecture.py` bindet `check` an `cli_check.py` und prüft weiterhin Modulgrenzen, Seiteneffektverträge, Shellverbot und Größenlimits.

Der Versionstest leitet die erwarteten Werte aus `registry.json` ab und liest `pyproject.toml` ohne Python-3.11-Abhängigkeit.

## Verbleibende Grenzen

- `last-run.json` beschreibt den zuletzt gestarteten Prozess; parallele unabhängige Nur-Lese-Befehle können diesen Hinweis ersetzen.
- Journalfehler dürfen den eigentlichen Befehl nicht blockieren; `check` macht fehlende Schreibbarkeit sichtbar.
- Hardware-, Kernel-, Dateisystem- und Datenträgerverlust bleiben außerhalb des Anwendungsschutzes.
- Reale Laienabnahme ist noch offen.

## Releaseprüfung

```bash
python -m json.tool registry.json >/dev/null
python -m json.tool project_registry.json >/dev/null
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
python -m datenbanktool --version
python -m datenbanktool check
```

`AGENTS.md` und die Sperre automatischer Originaldateioperationen bleiben unverändert.
