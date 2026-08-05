# Entwicklerdokumentation

## Architekturstand `0.19.0-alpha.1` / `0.19.0a1`

Diese Iteration ergänzt zwei voneinander getrennte Verträge:

1. eine vollständig lesende Terminal- und JSON-Diagnose aller gespeicherten Wiederanläufe,
2. ein ausdrücklich optionales, inhaltsfreies JSON-Protokoll nach erfolgreicher Konfigurations-Wiederherstellung.

Originaldatei-Schreibzugriffe bleiben gesperrt. Es gibt keine Shell-Auswertung, automatische Protokollbenennung, Zielauswahl, Rotation oder Löschung.

## Fachmodule

| Modul | Verantwortung |
|---|---|
| `core/run_journal.py` | dauerhafte, begrenzte und gesperrte Wiederanlaufliste |
| `core/recovery.py` | unabhängige Nur-Lese-Validierung jedes Eintrags gegen Ordner, Index und SQLite-Sitzung |
| `cli_recovery.py` | öffentlicher Diagnoseparser sowie Terminal- und JSON-Darstellung |
| `core/config_restore.py` | Vergleich, Restore, automatische Rückfallsicherung und automatischer Rückfall |
| `core/restore_audit.py` | minimales Restore-Nachweisschema, atomare Veröffentlichung und Nachprüfung |
| `cli_backups.py` | optionale `--restore-log`-Steuerung und getrennte Teilfehlerausgabe |
| `tests/test_recovery_diagnostics_and_restore_log.py` | Lesewirkungs-, Inhaltsschutz-, Zielschutz- und Teilfehlerverträge |

## Wiederanlauf-Diagnose

Öffentliche Befehle:

```text
index recovery
index recovery --json
```

Policy:

```text
CommandPolicy("index.recovery")
```

Alle Schreibflags bleiben `False`.

### Datenquelle und Validierung

`run_recovery_diagnostics()` ruft ausschließlich `load_recovery_candidates()` auf. Damit verwendet die Diagnose dieselbe fachliche Prüfung wie die geführte Startseite:

1. unterstützte gespeicherte Befehlsform erkennen,
2. Quellordner normalisieren und auf Verfügbarkeit prüfen,
3. Indexdatei normalisieren und als normale Datei prüfen,
4. SQLite über URI `mode=ro` öffnen,
5. `PRAGMA query_only = ON` setzen,
6. passende Scanart und Stammordner prüfen,
7. neueste Sitzung mit `running`, `interrupted` oder `failed` lesen.

Nicht verfügbare Einträge werden sichtbar als nicht startbar ausgegeben. Der Diagnosebefehl entfernt oder repariert keinen Datensatz.

### Terminalausgabe

Je Kandidat erscheinen:

- Operation,
- Startbarkeit,
- Prüfstatus,
- Quellordner,
- Indexdatei,
- Sitzungsnummer oder fehlende bestätigte Sitzung,
- Zustand,
- Phase,
- bestätigte Dateizahl,
- Aktualisierungszeit in UTC,
- technische Begründung.

Vor der Liste werden Gesamtzahl, startbare und nicht startbare Einträge ausgegeben.

### JSON-Schema

Oberste Felder:

```json
{
  "schema_version": 1,
  "generated_utc": "...",
  "source_file": ".../resume-run.json",
  "record_count": 0,
  "startable_count": 0,
  "not_startable_count": 0,
  "items": []
}
```

Jeder Eintrag enthält den vollständigen `RecoveryCandidate` und zusätzlich das verständliche Aliasfeld `startable`. Maschinenlesbare Ausgabe enthält keine ANSI-Sequenzen oder Bedienhinweise.

### Nachweis der Lesewirkung

Automatische Tests lesen vor und nach dem Befehl:

- die vollständigen Bytes von `resume-run.json`,
- die vollständigen Bytes der geprüften SQLite-Datei.

Beide müssen identisch bleiben. Zusätzlich besitzt das Modul keine Start-, Verwerfen- oder Löschfunktion.

## Optionales Wiederherstellungsprotokoll

Erweiterter Befehl:

```text
index backups restore DATABASE BACKUP
  [--config-directory DIR]
  --confirm-name NAME
  --yes
  [--restore-log NEW_PATH]
  [--json]
```

Policy:

```text
writes_backups=True
writes_configuration=True
writes_reports=True
writes_original_files=False
```

`writes_reports=True` beschreibt ausschließlich die optionale neue Protokolldatei.

### Reihenfolge

`run_backup_restore()` führt die Schritte strikt getrennt aus:

1. `restore_config_backup()` vollständig abschließen,
2. erfolgreiche Konfigurations-Wiederherstellung als `ConfigRestoreResult` erhalten,
3. nur bei gesetztem `--restore-log` `write_restore_audit_log()` aufrufen,
4. Erfolg oder Teilfehler des Protokolls getrennt ausgeben.

Ein Protokoll wird niemals vor oder während der Konfigurationsmutation geschrieben.

### Protokollschema

```json
{
  "schema_version": 1,
  "event": "configuration_restore",
  "created_utc": "...",
  "restore_completed_utc": "...",
  "configuration_kind": "search",
  "active_file": "/.../search-presets.json",
  "selected_backup": "/.../search-presets.json.backup-....json",
  "rollback_backup": "/.../search-presets.json.backup-....json",
  "sha256": {
    "active_after_restore": "...",
    "selected_backup": "...",
    "rollback_backup": "..."
  }
}
```

Ausgeschlossen sind:

- Vorlagenlisten,
- Konfigurationswerte,
- Antwortwerte,
- Kommandozeilenargumente,
- Tokens, Passwörter und andere Geheimnisse,
- automatische Kennungen aus externen Systemen.

Die Dateipfade sind bewusst Teil des Nachweises und werden deshalb als potenziell sensible Metadaten dokumentiert.

### Ziel- und Veröffentlichungsvertrag

`write_restore_audit_log()` verlangt:

1. ausdrücklich übergebenen Pfad,
2. Ziel darf kein Symlink sein,
3. Ziel darf noch nicht existieren,
4. Elternordner wird nur für genau dieses Ziel angelegt,
5. Veröffentlichung über `atomic_write_text()` mit Modus `0600`,
6. erneutes Lesen als UTF-8-JSON,
7. vollständigen Vergleich des geschriebenen Objekts mit dem geplanten Payload,
8. SHA-256 des vollständigen Protokolls als Rückgabewert.

Es gibt kein `overwrite=True`, keine Rotation und keine Löschfunktion.

### Teilfehlervertrag

Scheitert nur das optionale Protokoll:

- die bereits bestätigte aktive Konfiguration bleibt im Restore-Zielstand,
- ausgewählte Sicherung und Rückfallsicherung bleiben erhalten,
- Terminal erklärt zuerst, dass der Restore erfolgreich war,
- technische Protokollursache folgt getrennt,
- JSON enthält `restore_log: null` und `restore_log_error`,
- Rückgabecode ist `1`.

Ohne `--restore-log` bleibt die bisherige JSON-Struktur des Restore-Ergebnisses unverändert.

## Architekturgrenzen

- `cli.py` registriert nur `register_recovery_parser()` und bleibt unter 150 Zeilen.
- Alle `cli_*.py` bleiben unter 500 Zeilen.
- Fachmodule importieren `cli.py` nicht.
- Kein `subprocess`, `shell=True`, `os.system`, `eval` oder `exec` in CLI-Fachmodulen.
- Diagnose und Restore-Protokoll besitzen getrennte Module und keine zyklischen Importe.
- Keine neue Laufzeitabhängigkeit.

## Automatische Prüfungen

Die Version enthält 145 Tests, darunter:

- vollständige Terminaldiagnose eines fortsetzbaren Scans,
- stabiles JSON-Schema mit allen geforderten Feldern,
- leere Diagnose mit Rückgabecode 0,
- bytegenau unveränderte Wiederanlauf- und Indexdatei,
- Parser-, Handler- und Policy-Zuordnung des Diagnosebefehls,
- optionales Restore-Protokoll mit exakt drei Hashrollen,
- Dateimodus `0600`,
- keine Konfigurationsinhalte oder Geheimnisse,
- kein Protokoll ohne ausdrückliche Option,
- vorhandenes Ziel wird nicht überschrieben,
- erfolgreicher Restore bleibt bei Protokollfehler erhalten,
- JSON-Teilfehler und Rückgabecode `1`,
- bestehende Restore-, Rückfall-, Autosave- und Originaldateischutztests,
- Modulgrößen, Shellverbot und Versionsdrift.

Die Matrix läuft unter Python 3.10 und 3.12 mit `PYTHONWARNINGS=error`. Quick- und Standardabnahme verwenden ausschließlich synthetische Daten.

## Verbleibende Grenzen

- Diagnose startet oder verwirft absichtlich keinen Eintrag.
- Strukturell nicht erkennbare interne Datensätze werden nicht automatisch repariert.
- Optionaler Protokollpfad ist noch nicht in den geführten Startseiten-Restore integriert.
- Ein eigenständiger späterer Prüfbefehl für Restore-Protokolle fehlt noch.
- Protokollpfade können sensible lokale Metadaten darstellen.
- Hardware-, Kernel-, Dateisystem- und physischer Verlust bleiben außerhalb des Anwendungsschutzes.
- Reale Laienabnahme ist offen.

## Releaseprüfung

```bash
python -m json.tool registry.json >/dev/null
python -m json.tool project_registry.json >/dev/null
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
python -m datenbanktool --version
python -m datenbanktool index recovery --json
python -m datenbanktool check
```

`AGENTS.md` und die Sperre automatischer Originaldateioperationen bleiben unverändert.
