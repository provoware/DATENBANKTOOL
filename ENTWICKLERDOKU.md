# Entwicklerdokumentation

## Architekturstand `0.20.0-alpha.1` / `0.20.0a1`

Diese Iteration ergänzt einen vollständig lesenden Prüfvertrag für ein ausdrücklich ausgewähltes Wiederherstellungsprotokoll. Das feste JSON-Schema wird zuerst vollständig validiert. Erst danach werden die drei referenzierten Dateien ohne Symlink-Folgen geöffnet, gestreamt gehasht und mit den protokollierten SHA-256-Werten verglichen.

Es gibt keine Wiederherstellung, Reparatur, Änderung, Neuanlage oder Löschung. Originaldatei-Schreibzugriffe bleiben gesperrt; Shell-Auswertung und neue Laufzeitabhängigkeiten bleiben ausgeschlossen.

## Fachmodule

| Modul | Verantwortung |
|---|---|
| `core/restore_audit.py` | Protokollschema, atomare Erzeugung, strikte Validierung und rein lesender Dateinachweis |
| `cli_restore_audit.py` | Parser `verify-log`, Terminal-/JSON-Darstellung und Rückgabecodes |
| `cli_backups.py` | Registrierung des eigenständigen Fachparsers innerhalb `index backups` |
| `tests/test_restore_audit_verification.py` | Schema-, UTC-, Pfad-, Hash-, Symlink-, Integritäts- und Lesewirkungstests |
| `tests/test_cli_architecture.py` | Handler-, Policy-, Modulgrößen- und Shellverbotsvertrag |

## Öffentlicher Befehl

```text
index backups verify-log PROTOCOL [--json]
```

Policy:

```text
CommandPolicy("index.backups.verify-log")
```

Alle Schreibflags bleiben `False`.

## Prüfungsreihenfolge

`verify_restore_audit_log()` arbeitet fail-closed in dieser Reihenfolge:

1. Protokollpfad lexikalisch absolut normalisieren, ohne Symlinks aufzulösen.
2. Protokoll-Symlink ablehnen.
3. Datei mit `O_RDONLY`, `O_CLOEXEC` und `O_NOFOLLOW` öffnen.
4. Über `fstat()` bestätigen, dass der geöffnete Deskriptor eine normale Datei ist.
5. Inhalt als UTF-8-JSON-Objekt lesen.
6. Exakten obersten Schlüsselsatz prüfen.
7. `schema_version == 1` und `event == configuration_restore` prüfen.
8. `configuration_kind` auf `search` oder `timeline` begrenzen.
9. `created_utc` und `restore_completed_utc` als ISO-8601-Zeiten lesen.
10. Für beide Zeiten einen UTC-Offset von null verlangen.
11. Sicherstellen, dass die Protokollzeit nicht vor dem Restore-Abschluss liegt.
12. Drei nicht leere absolute Pfade lesen und auf gegenseitige Eindeutigkeit prüfen.
13. Exakten SHA-256-Schlüsselsatz prüfen.
14. Drei kleingeschriebene Werte mit jeweils 64 Hexzeichen validieren.
15. Erst jetzt jede referenzierte Datei rein lesend prüfen und hashen.

Ungültige Struktur verhindert jeden Zugriff auf protokollierte Referenzpfade.

## Festes Protokollschema

```json
{
  "schema_version": 1,
  "event": "configuration_restore",
  "created_utc": "2026-08-05T10:00:00+00:00",
  "restore_completed_utc": "2026-08-05T09:59:59+00:00",
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

Fehlende oder zusätzliche Felder werden abgelehnt. Dadurch können Konfigurationsinhalte, Argumente oder beliebige Erweiterungsdaten nicht unbemerkt als gültiges Schema erscheinen.

## Rein lesendes Dateiöffnen

`_open_regular_no_follow()` verwendet auf Linux:

```text
O_RDONLY | O_CLOEXEC | O_NOFOLLOW
```

Nach dem Öffnen bestätigt `fstat()` den Typ `S_ISREG`. Das verhindert sowohl offensichtliche Symlinks als auch einen Zielwechsel zwischen Vorprüfung und Öffnen. Referenzdateien werden in 1-MiB-Blöcken gelesen und direkt in SHA-256 eingespeist.

Es gibt keinen Aufruf von:

- `resolve()` für protokollierte Pfade,
- `atomic_write_*`,
- `durable_remove()`,
- Restore- oder Backup-Funktionen,
- Shell oder Subprozess.

## Ergebniszustände je Datei

| Zustand | Ampel | Bedeutung |
|---|---|---|
| `match` | Grün | normale Datei vorhanden, tatsächlicher SHA-256 stimmt überein |
| `missing` | Gelb | Datei derzeit nicht vorhanden; Nachweis nicht vollständig bestätigbar |
| `mismatch` | Rot | Datei vorhanden, SHA-256 weicht ab |
| `symlink-rejected` | Rot | Pfad ist ein Symlink und wird nicht verfolgt |
| `unreadable` | Rot | falscher Dateityp, Berechtigungs- oder Lesefehler |

Gesamtstatus:

- Grün nur, wenn alle drei Einträge `match` sind.
- Rot, sobald ein roter Dateibefund existiert.
- Gelb nur bei fehlender Datei ohne roten Befund.

## JSON-Ausgabe

`RestoreAuditVerification.to_dict()` enthält:

- Protokollpfad,
- Schema, Ereignis und beide UTC-Zeiten,
- Konfigurationsart,
- `read_only: true`,
- Gesamtstatus und technische Begründung,
- Datei-, Treffer-, Fehl- und Abweichungszähler,
- `all_files_match`,
- drei Dateiobjekte mit Rolle, Pfad, Soll- und Ist-Hash sowie Einzelstatus.

Die Ausgabe enthält keine ANSI-Sequenzen und keine Dateiinhalte.

## Rückgabecodes

| Code | Vertrag |
|---:|---|
| `0` | Schema gültig und alle drei Dateien bestätigt |
| `1` | Schema gültig, Dateinachweis aber fehlend, abweichend oder nicht sicher lesbar |
| `2` | CLI-Eingabe, Protokolldatei oder Schema ungültig |

## Architekturgrenzen

- `cli_restore_audit.py` ist ein eigenes Fachmodul und importiert `cli.py` nicht.
- `cli_backups.py` registriert nur den Unterparser und enthält keine zweite Prüflogik.
- Alle `cli_*.py` bleiben unter 500 Zeilen; `cli.py` bleibt unter 150 Zeilen.
- Kein `subprocess`, `shell=True`, `os.system`, `eval` oder `exec` in CLI-Fachmodulen.
- Keine neue Laufzeitabhängigkeit.
- Keine Änderung der Originaldatei-Sperre.

## Automatische Prüfungen

Die Version enthält 151 Tests, darunter:

- gültiges Protokoll mit drei bestätigten Dateien,
- bytegenau unverändertes Protokoll und unveränderte Referenzdateien,
- keine neuen oder gelöschten Pfade durch die Prüfung,
- rote Hashabweichung nach bewusster Dateiveränderung,
- gelber unvollständiger Nachweis bei fehlender Datei,
- Zusatzfeld, Nicht-UTC-Zeit und falsche Zeitreihenfolge,
- relativer und doppelter Pfad,
- fehlende Hashrolle und großgeschriebener Hash,
- abgelehnter Protokoll-Symlink,
- Terminal- und JSON-Ausgabe,
- Rückgabecode 0 und 1,
- Handler, rein lesende Policy und Modulzuständigkeit,
- Größenlimits, Shellverbot und Versionsdrift.

Die Matrix läuft unter Python 3.10 und 3.12 mit `PYTHONWARNINGS=error`. Quick- und Standardabnahme verwenden ausschließlich synthetische Daten.

## Verbleibende Grenzen

- Der Grund einer Hashabweichung wird nicht automatisch interpretiert.
- Fehlende Dateien werden nicht gesucht oder rekonstruiert.
- Nur Protokollschema 1 wird akzeptiert.
- Die Protokolldatei selbst ist noch nicht an einen extern vorgegebenen Hash oder eine Signatur gebunden.
- Die Prüfung ist noch nicht in die geführte Startseite integriert.
- Pfade können sensible lokale Metadaten darstellen.
- Reale Laienabnahme bleibt offen.

## Releaseprüfung

```bash
python -m json.tool registry.json >/dev/null
python -m json.tool project_registry.json >/dev/null
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
python -m datenbanktool --version
python -m datenbanktool index backups verify-log /pfad/restore-nachweis.json --json
python -m datenbanktool check
```

`AGENTS.md` und die Sperre automatischer Originaldateioperationen bleiben unverändert.
