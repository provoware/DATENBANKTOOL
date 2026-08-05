# Entwicklerdokumentation

## Architekturstand `0.16.0-alpha.1` / `0.16.0a1`

Diese Iteration ergänzt zwei eng begrenzte Verträge:

1. einen geführten, gegen SQLite validierten Wiederanlauf für unterbrochene Vollscans und Re-Scans,
2. einen nur lesenden Sicherungskatalog mit genau einer ausdrücklich bestätigten Löschung.

Originaldatei-Schreibzugriffe bleiben gesperrt. Es gibt keine Shell-Auswertung, automatische Rotation oder Sammellöschung.

## Neue und erweiterte Fachmodule

| Modul | Verantwortung |
|---|---|
| `core/run_journal.py` | allgemeines Laufjournal plus dauerhafter `resume-run.json`-Datensatz |
| `core/recovery.py` | Befehlsanalyse und Nur-Lese-Abgleich mit der fortsetzbaren SQLite-Sitzung |
| `core/backup_catalog.py` | Sicherungsfindung, Gesundheitsprüfung und begrenzte Einzellöschung |
| `cli_backups.py` | öffentliche Befehle `index backups list/delete` |
| `core/terminal_home.py` | Startseiten-Erweiterung für Wiederanlauf und Sicherungsverwaltung |
| `core/durable_files.py` | atomare Veröffentlichung und dauerhafte Einzellöschung ohne Symlink-Folgen |
| `tests/test_guided_recovery_backups.py` | Dialog-, Katalog- und Löschverträge |
| `tests/test_recovery_backup_edges.py` | Re-Scan, stale marker, CLI und Symlink-Negativfälle |
| `tests/test_durable_symlinks.py` | zentrale Schreib- und Löschsperre für Symlinks |

## Wiederanlaufdatensatz

Standardpfad:

```text
$XDG_STATE_HOME/datenbanktool/resume-run.json
```

Fallback:

```text
~/.local/state/datenbanktool/resume-run.json
```

Der Datensatz wird nur für bestätigte Befehle mit folgendem Muster erstellt:

```text
index build ...
index rescan ...
```

Er enthält Schema, Status, Zeiten, Exitcode und die exakte Argumentliste. Das allgemeine `last-run.json` bleibt davon getrennt, damit ein normaler späterer Startseitenabschluss den fortsetzbaren Scan nicht überschreibt.

### Lebenszyklus

1. Vor Ausführung speichert `RunJournal.record_active_command()` den bestätigten Scanbefehl.
2. Rückgabecode `0` entfernt nur `resume-run.json`.
3. Nichtnull, Tastaturabbruch oder unerwartete Ausnahme erhalten den Datensatz mit aktualisiertem Zustand.
4. Ein normaler Startseitenabbruch verändert den Datensatz nicht.
5. `load_recovery_candidate()` prüft den Datensatz erneut gegen Dateisystem und SQLite.

## Wiederanlaufvalidierung

`core/recovery.py` akzeptiert ausschließlich `build` und `rescan`.

Prüfungen:

1. Argumentliste ist vollständig und enthält `--database`.
2. Quellordner existiert als Ordner.
3. Index existiert als Datei.
4. SQLite wird per URI `mode=ro` geöffnet.
5. `PRAGMA query_only = ON` wird gesetzt.
6. `scan_sessions` enthält für denselben normalisierten Stammordner und dieselbe Scanart eine neueste Sitzung mit `running`, `interrupted` oder `failed`.
7. Der zurückgegebene Befehl enthält genau ein abschließendes `--resume`.

Zuordnung:

| Befehl | SQLite-Scanart | Nutzertext |
|---|---|---|
| `index build` | `full` | erste Ordnerprüfung |
| `index rescan` | `incremental` | Änderungsprüfung |

Ist Ordner oder Datenträger vorübergehend nicht verfügbar, bleibt der Marker erhalten. Beweist die Datenbank dagegen, dass keine passende fortsetzbare Sitzung existiert, wird der veraltete Marker entfernt.

## Startseitenablauf

`core/terminal_home.TerminalHome` erweitert die bestehende Dialogklasse.

Vor dem normalen Menü:

1. `load_recovery_candidate()` ausführen.
2. Art, Ordner, Index, Sitzung, Status, Phase und Dateizahl anzeigen.
3. Vollständigen Befehl mit `shlex.join()` sichtbar darstellen.
4. Ja/Nein abfragen; Standard ist Nein.
5. Nur bei Ja dieselbe Argumentliste an den vorhandenen `CommandRunner` übergeben.

Nein, `q` oder geschlossene Eingabe startet nichts und erhält den Marker. Der `entrypoint` umschließt den Startseiten-Runner so, dass der tatsächlich innere Befehl vor der Ausführung im Journal registriert und nachher mit seinem Rückgabecode abgeschlossen wird.

## Sicherungskatalog

Öffentliche Befehle:

```text
index backups list DATABASE [--config-directory DIR] [--json]
index backups delete DATABASE BACKUP --confirm-name NAME --yes
```

### Erkennung

Index-Sicherungen liegen neben der aktiven Datenbank und folgen den vom Tool erzeugten Mustern:

```text
<datenbankname>.backup-*.sqlite3
<datenbankname>.pre-restore-*.sqlite3
```

Unterstützte Konfigurationssicherungen beziehen sich auf:

```text
search-presets.json
timeline-presets.json
```

Nur bekannte `.backup-*`, `-backup-*`, `.bak`- oder `.backup`-Muster werden katalogisiert. Dadurch wird eine beliebige Datei nicht allein aufgrund ihrer Lage löschbar.

### Gesundheitsprüfung

Index-Sicherung:

- URI `mode=ro`,
- `query_only`,
- `PRAGMA user_version`,
- `PRAGMA quick_check`,
- grün bei nutzbarer unterstützter Version,
- gelb bei neuerer Schemaversion,
- rot bei Lesefehler oder beschädigtem `quick_check`.

Konfigurations-Sicherung:

- UTF-8-JSON,
- oberste Ebene ist Objekt,
- `schema_version` ist Ganzzahl,
- `presets` ist Liste,
- grün bei Schema 1,
- gelb bei unbekannter Version,
- rot bei beschädigter oder unvollständiger Struktur.

Jeder `BackupItem` enthält Pfad, Name, Typ, Bytes, UTC-Änderungszeit, Alter in Sekunden, Status und technische Begründung. Sortiert wird nach kleinstem Alter: neueste zuerst.

## Einzellöschvertrag

`delete_backup()` verlangt gleichzeitig:

1. `yes=True`,
2. Pfad kommt in der unmittelbar neu aufgebauten geprüften Übersicht vor,
3. `confirm_name` stimmt exakt mit dem Dateinamen überein,
4. Ziel ist kein Symlink,
5. Ziel ist eine normale Datei.

Danach entfernt `durable_remove()` genau diesen Verzeichniseintrag und bestätigt das Elternverzeichnis mit `fsync`.

Aktive Indexdatei, aktive Vorlagendatei, unbekannte Datei, Verzeichnis und Symlink sind nicht löschbar. Es gibt keine Mehrfachauswahl und keine Altersautomatik.

## Symlink-Härtung

Dauerhafte Zielpfade werden lexikalisch absolut normalisiert, ohne die letzte Pfadkomponente aufzulösen. Dadurch können `atomic_write_*()`, `publish_temp_file()` und `durable_remove()` einen vorhandenen Symlink erkennen und ablehnen.

Der Schutz liegt im zentralen Helfer und nicht nur in den aufrufenden Sicherungsfunktionen. Tests bestätigen, dass Link und echtes Ziel unverändert bleiben.

## CommandPolicy

| Befehl | Policy |
|---|---|
| `index backups list` | rein lesend |
| `index backups delete` | `writes_backups=True` |
| geführter Wiederanlauf | bestehende Policy von `index.build` oder `index.rescan` |

`tests/test_cli_architecture.py` prüft Parser, Handler, Policy, Modulzuständigkeit, Größenlimits und Shellverbot.

## Automatische Prüfungen

Geprüft werden unter anderem:

- Vollscan- und Re-Scan-Kandidat,
- genau ein `--resume`,
- sichtbarer Befehl entspricht ausgeführter Argumentliste,
- Nein und Abbruch erhalten den Marker,
- Erfolg entfernt nur den Marker,
- stale marker ohne SQLite-Sitzung,
- gültige und beschädigte Sicherungen,
- Größe, Alter und UTC-Zeit,
- JSON-CLI-Ausgabe,
- tatsächliche Einzellöschung,
- fehlendes `--yes`, falscher Name und aktive Datei,
- Symlink auf Sicherung,
- zentrale Symlink-Sperre bei Schreiben und Löschen.

## Verbleibende Grenzen

- Genau ein Scan kann vorgemerkt sein; eine begrenzte Mehrfachliste ist offen.
- Nicht eingehängte Datenträger verhindern vorübergehend die Anzeige, löschen den Marker aber nicht.
- Vorlagenänderungen erstellen noch keine automatische Konfigurationssicherung.
- Hardware-, Kernel-, Dateisystem- und physischer Verlust bleiben außerhalb des Anwendungsschutzes.
- Reale Laienabnahme ist offen.

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
