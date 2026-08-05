# Entwicklerdokumentation

## Architekturstand `0.18.0-alpha.1` / `0.18.0a1`

Diese Iteration ergänzt einen streng begrenzten Vertrag zur Wiederherstellung lokaler Such- und Zeitreihen-Konfigurationen:

1. eine katalogisierte Sicherung wird zuerst vollständig lesend mit ihrer aktiven Datei verglichen,
2. Wiederherstellung erfolgt nur einzeln nach exakter Namens- und Ja-Bestätigung,
3. vor jeder Mutation entsteht eine geprüfte Rückfallsicherung,
4. bei fehlgeschlagener Nachprüfung wird automatisch auf diese Sicherung zurückgesetzt.

Originaldatei-Schreibzugriffe bleiben gesperrt. Es gibt keine Shell-Auswertung, automatische Auswahl, Rotation, Alterslöschung oder Sammellöschung.

## Fachmodule

| Modul | Verantwortung |
|---|---|
| `core/backup_catalog.py` | Erkennung und Gesundheitsstatus unterstützter Sicherungen |
| `core/config_backups.py` | geprüfte, zeitgestempelte JSON-Sicherung mit Modus `0600` |
| `core/config_restore.py` | Zuordnung, Nur-Lese-Vergleich, Prüfsummen, Restore, Rückfallsicherung und automatischer Rückfall |
| `cli_backups.py` | öffentliche Befehle `list`, `compare`, `restore` und `delete` |
| `core/terminal_home.py` | geführte Auswahl, Wirkungsvorschau, Namensprüfung und sichere Argumentliste |
| `tests/test_config_restore.py` | Kern-, CLI-, Dialog-, Negativ- und Rückfallverträge |

## Öffentliche Befehle

### Nur-Lese-Vergleich

```text
index backups compare DATABASE BACKUP [--config-directory DIR] [--json]
```

`CommandPolicy("index.backups.compare")` enthält keine Schreibwirkung.

### Wiederherstellung

```text
index backups restore DATABASE BACKUP
  [--config-directory DIR]
  --confirm-name NAME
  --yes
  [--json]
```

Policy:

```text
writes_backups=True
writes_configuration=True
writes_original_files=False
```

## Vertrauensgrenze des Vergleichs

`compare_config_backup()` akzeptiert nur eine Datei, die in einer unmittelbar neu aufgebauten `list_backups()`-Übersicht vorkommt.

Zusätzliche Bedingungen:

1. `kind == "configuration"`,
2. `status_level == "green"`,
3. unterstützter Dateiname für `search-presets.json` oder `timeline-presets.json`,
4. Sicherung und aktive Datei sind normale Dateien und keine Symlinks,
5. aktive Datei existiert,
6. vollständige fachliche Deserialisierung über die vorhandenen Funktionen:
   - `list_presets()`,
   - `list_timeline_presets()`.

Dadurch existiert keine zweite vereinfachte Vorlagenschema-Implementierung im Restore-Modul.

## Vergleichsmodell

Für beide Dateien entsteht eine case-insensitive Namensabbildung. Mehrfach vorkommende Namen werden als uneindeutig abgelehnt.

Der Vergleich liefert:

- `add_names`: in der Sicherung, nicht aktiv,
- `remove_names`: aktiv, nicht in der Sicherung,
- `change_names`: gleicher Name, unterschiedlicher vollständiger Datensatz,
- `unchanged_names`: gleicher vollständiger Datensatz,
- Vorlagenzahlen,
- SHA-256 beider Dateien,
- `identical` und `can_restore`.

Der Vergleich verändert keine Datei und erzeugt keine Sicherung.

## Wiederherstellungsablauf

`restore_config_backup()` führt die folgenden Schritte in fester Reihenfolge aus:

1. `--yes` prüfen.
2. Frischen vollständigen Vergleich aufbauen.
3. Exakten Sicherungsdateinamen prüfen.
4. Bytegenau identische Dateien ablehnen.
5. Aktive Datei und Sicherung erneut lesen und gegen die Vergleichs-SHA-256 prüfen.
6. Mit `create_config_backup(active)` eine neue Rückfallsicherung erzeugen und vollständig validieren.
7. Bestätigen, dass deren SHA-256 dem aktiven Vergleichsstand entspricht.
8. Aktive Datei unmittelbar vor dem Überschreiben erneut prüfen.
9. Sicherungsbytes mit `atomic_write_bytes(..., overwrite=True, mode=0o600)` veröffentlichen.
10. Wiederhergestellte Datei bytegenau, per SHA-256 und fachlicher Deserialisierung prüfen.

Ausgewählte Sicherung und Rückfallsicherung werden nicht gelöscht.

## Automatischer Rückfall

Wirft Veröffentlichung oder Nachprüfung einen Fehler:

1. Rückfallsicherung erneut als normale Datei lesen,
2. deren Bytes atomar auf die aktive Datei schreiben,
3. aktive Datei gegen die Rückfall-SHA-256 und das fachliche Schema prüfen,
4. ursprünglichen Restore als kontrolliert fehlgeschlagen melden.

Scheitert auch die Rückfallbestätigung, wird ein `RuntimeError` mit dem unverändert erhaltenen Rückfallsicherungspfad ausgelöst. Der Code behauptet in diesem Fall keinen erfolgreich wiederhergestellten Zustand.

## Geführte Startseite

Menüpunkt 7 enthält `wiederherstellen`.

Ablauf:

1. Datenbankpfad erfassen.
2. Nur Konfigurationssicherungen aus dem aktuellen Katalog anzeigen.
3. Sicherung per Nummer oder vollständigem Pfad wählen.
4. `compare_config_backup()` direkt rein lesend ausführen.
5. Art, aktive Datei sowie Hinzufügen/Entfernen/Ersetzen/Unverändert anzeigen.
6. Identische Dateien ohne Dispatch beenden.
7. Sicherungsdateinamen exakt wiederholen lassen.
8. Sichere Argumentliste für `index backups restore ... --confirm-name ... --yes` bauen.
9. Vor Dispatch den bestehenden vollständigen Befehls-Bestätigungsdialog verwenden.

Es findet keine Shell-Auswertung statt.

## Aufbewahrungsvertrag

Der Restore-Code enthält keine:

- automatische Sicherungsauswahl,
- Anzahlrotation,
- Altersrotation,
- Speicherplatzrotation,
- Sammellöschung,
- Löschung der ausgewählten Sicherung,
- Löschung der Rückfallsicherung.

## Automatische Prüfungen

Die Version enthält 139 Tests, darunter:

- exakter Suchvorlagen-Vergleich,
- Zuordnung einer Zeitreihen-Sicherung,
- nachweislich lesender Vergleich,
- Wiederherstellung mit bytegenauer Rückfallsicherung,
- Modus `0600`,
- fehlendes `--yes`,
- falscher Dateiname,
- identischer Stand,
- unbekannter Pfad,
- beschädigte JSON-Datei,
- abgelehnte Indexsicherung,
- simulierte fehlgeschlagene Nachprüfung,
- automatischer und bestätigter Rückfall,
- Terminal- und JSON-CLI,
- geführte Wirkungsvorschau,
- kein Dispatch bei falschem Namen,
- Handler, Policy, Modulzuständigkeit, Größenlimits und Shellverbot.

Die Matrix läuft unter Python 3.10 und 3.12 mit `PYTHONWARNINGS=error`. Quick- und Standardabnahme verwenden ausschließlich synthetische Daten.

## Verbleibende Grenzen

- Die aktive Konfigurationsdatei muss vorhanden und gültig sein.
- Wiederhergestellt wird die vollständige Datei, nicht eine frei zusammengestellte Auswahl einzelner Vorlagen.
- Gelbe oder unbekannte Schemaversionen werden nicht automatisch migriert.
- Beliebig benannte manuelle Kopien bleiben außerhalb des Katalogvertrags.
- Eine eigenständige rein lesende Diagnose-CLI für die Wiederanlaufliste fehlt noch.
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
