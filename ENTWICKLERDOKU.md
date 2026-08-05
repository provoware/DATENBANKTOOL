# Entwicklerdokumentation

## Architekturstand `0.17.0-alpha.1` / `0.17.0a1`

Diese Iteration erweitert den bestehenden Wiederanlauf- und Sicherungsvertrag um:

1. eine begrenzte Mehrfachliste für unterbrochene Scans verschiedener Indexdateien,
2. getrennte Nur-Lese-Validierung und Einzelentscheidung je Eintrag,
3. optionale, geprüfte JSON-Sicherungen vor dem Ersetzen oder Löschen von Vorlagen.

Originaldatei-Schreibzugriffe bleiben gesperrt. Es gibt keine Shell-Auswertung, automatische Sicherungsrotation oder Sammellöschung.

## Fachmodule

| Modul | Verantwortung |
|---|---|
| `core/run_journal.py` | allgemeines Laufjournal, Schema-2-Wiederanlaufliste, Deduplizierung, Limit und Dateisperre |
| `core/recovery.py` | getrennte Analyse und Nur-Lese-Validierung jedes Wiederanlaufeintrags |
| `core/terminal_home.py` | nummerierte Auswahl, Fortsetzen, Erhalten und bewusstes Einzelverwerfen |
| `core/config_backups.py` | validierte, zeitgestempelte und nachgeprüfte JSON-Sicherung |
| `cli_preset_change.py` | gemeinsame CLI-Option, Existenzprüfung und verständliche Sicherungsausgabe |
| `cli_config_backups.py` | schmale Kompatibilitätsschicht ohne zweite Implementierung |
| `cli_search.py` | Suchvorlagenverwaltung mit optionaler Vorsicherung |
| `cli_timeline_presets.py` | Zeitreihen-Vorlagenverwaltung mit optionaler Vorsicherung |
| `tests/test_multiple_recovery_and_config_backups.py` | Mehrfachlisten-, Auswahl-, Limit-, Sicherungs- und Negativverträge |

## Wiederanlaufliste

Standardpfad:

```text
$XDG_STATE_HOME/datenbanktool/resume-run.json
```

Fallback:

```text
~/.local/state/datenbanktool/resume-run.json
```

Schema 2:

```json
{
  "schema_version": 2,
  "maximum_records": 12,
  "updated_utc": "...",
  "records": []
}
```

### Identität und Deduplizierung

- Nur bestätigte `index build`- und `index rescan`-Befehle werden aufgenommen.
- Der Datenbankpfad wird expandiert, absolut und normalisiert gespeichert.
- Aus dem normalisierten Pfad entsteht eine stabile SHA-256-Eintragskennung.
- Pro Indexdatei existiert höchstens ein Eintrag.
- Ein neuerer Lauf derselben Indexdatei ersetzt nur den bisherigen Eintrag dieser Datei.
- `--resume` wird normalisiert und erscheint höchstens einmal.

### Begrenzung

`MAX_RESUME_RECORDS = 12`.

Nach dem Sortieren nach Aktualisierungszeit werden nur die zwölf neuesten internen Hinweise gespeichert. Diese Begrenzung entfernt oder verändert keine Index-, Quell- oder Originaldatei.

### Parallelität und Veröffentlichung

- Eine separate `.resume-run.lock`-Datei verwendet `fcntl.flock`.
- Lesen, Upsert und Einzelverwerfen laufen innerhalb dieser Sperre.
- JSON wird atomar, dauerhaft und mit Dateimodus `0600` veröffentlicht.
- Schema 1 wird beim Lesen in die neue Eintragsform überführt.

## Einzelvalidierung

`load_recovery_candidates()` liefert für jeden gespeicherten Eintrag einen `RecoveryCandidate`.

Geprüft werden:

1. unterstützte Befehlsform,
2. vollständige Argumentliste und Datenbankparameter,
3. vorhandener Quellordner,
4. vorhandene normale Indexdatei,
5. SQLite-Öffnung über URI `mode=ro`,
6. `PRAGMA query_only = ON`,
7. passende Scanart `full` oder `incremental`,
8. identischer normalisierter Stammordner,
9. neueste Sitzung mit `running`, `interrupted` oder `failed`.

Ein fehlender Ordner, ein nicht eingehängter Datenträger oder eine fehlende Datenbank erzeugt einen sichtbaren, nicht startbaren Kandidaten. Der Eintrag wird nicht automatisch entfernt.

## Startseitenablauf

Vor dem normalen Menü:

1. alle Kandidaten laden,
2. Anzahl und nummerierte Kurzliste anzeigen,
3. je Eintrag Operation, Prüfstatus, Ordner und Index ausgeben,
4. Auswahl einer Nummer oder Rückkehr ermöglichen,
5. Detailansicht mit Sitzung, Phase, Dateizahl und vollständigem Befehl anzeigen,
6. genau einen Eintrag fortsetzen, erhalten oder verwerfen.

### Fortsetzen

Nur `resumable=True` erlaubt den Start. Die angezeigte Argumentliste wird ohne Shell an den vorhandenen `CommandRunner` übergeben. Rückgabecode 0 entfernt nur den zugehörigen Eintrag.

### Verwerfen

`discard_recovery_candidate(record_id)` entfernt ausschließlich die ausgewählte interne Vormerkung. Ordner, Index und Originaldateien bleiben unverändert. Nicht startbare Einträge können nur erhalten oder bewusst verworfen werden.

## Konfigurationssicherung

Öffentliche Option:

```text
--backup-before-change
```

Sie gilt bei:

- `index presets save --replace`,
- `index presets delete --yes`,
- `index timeline-presets save --replace`,
- `index timeline-presets delete --yes`.

Die geführte Startseite ergänzt diese Option nur nach einer sichtbaren Ja/Nein-Frage.

### Vorprüfung

`create_config_backup()` verlangt:

- vorhandene normale Quelldatei,
- kein Symlink,
- UTF-8-JSON,
- oberste Ebene ist ein Objekt,
- erwartete `schema_version`,
- `presets` ist eine Liste.

### Dateiname und Veröffentlichung

```text
<aktive-datei>.backup-<UTC-Zeit>-<PID>.json
```

Die Sicherung wird mit `atomic_write_bytes()` und Modus `0600` veröffentlicht. Es gibt kein Überschreiben bestehender Sicherungen.

### Nachprüfung

Nach der Veröffentlichung werden erneut geprüft:

- vollständige Bytes,
- SHA-256,
- Schemaversion,
- Vorlagenzahl,
- JSON-Struktur.

Bei jeder Abweichung wird die nicht bestätigte Sicherung entfernt und die eigentliche Vorlagenänderung nicht ausgeführt.

### Keine Rotation

Der Sicherungscode enthält keine Anzahl-, Alters- oder Speicherplatzrotation. Mehrere ausdrücklich erstellte Sicherungen bleiben bestehen und werden vom vorhandenen Sicherungskatalog erkannt.

## CLI-Architektur

Die zunächst duplizierten Parser- und Ausgabefunktionen wurden in `cli_preset_change.py` vereinheitlicht. Dadurch bleibt `cli_search.py` unter dem verbindlichen Limit von 500 Zeilen. `tests/test_cli_architecture.py` prüft weiterhin:

- Größenlimits,
- Handler und `CommandPolicy`,
- eindeutige Modulzuständigkeit,
- Shellverbot,
- Sperre von Originaldatei-Schreibzugriffen.

## Automatische Prüfungen

Die Version enthält 130 Tests, darunter:

- zwei verschiedene Indexdateien gleichzeitig,
- Deduplizierung derselben Indexdatei,
- genau ein `--resume`,
- Listenlimit zwölf,
- erfolgreiches Entfernen nur des eigenen Eintrags,
- bewusstes Einzelverwerfen,
- nicht verfügbare Einträge bleiben sichtbar und nicht startbar,
- Suchvorlagen-Ersetzen sichert den alten Inhalt,
- Zeitreihen-Vorlagen-Löschen sichert die alte Konfiguration,
- optionale Sicherung kann ausgelassen werden,
- mehrere Sicherungen werden nicht rotiert,
- beschädigtes JSON wird abgelehnt,
- neue Sicherung erscheint grün im Katalog,
- CLI-Modulgrenzen bleiben eingehalten.

Die Matrix läuft unter Python 3.10 und 3.12 mit `PYTHONWARNINGS=error`. Quick- und Standardabnahme verwenden ausschließlich synthetische Daten.

## Verbleibende Grenzen

- Die Liste ist bewusst auf zwölf Einträge begrenzt.
- Nicht startbare Einträge werden nicht automatisch verworfen.
- Eine eigenständige rein lesende Diagnose-CLI für die Wiederanlaufliste fehlt noch.
- Konfigurationssicherungen besitzen noch keinen geführten Restore-Assistenten.
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
