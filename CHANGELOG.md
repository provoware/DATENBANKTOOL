# Changelog

## 0.8.0-alpha.1 – 2026-08-04

### Modulare Kommandozeilenarchitektur

- Frühere `cli.py` mit 1.409 Zeilen auf einen rund 100-zeiligen Einstieg reduziert.
- Einmalige Scans nach `cli_scan.py` verschoben.
- Suche und Suchvorlagen nach `cli_search.py` verschoben.
- Ordner-, Änderungs- und Dateiberichte nach `cli_reports.py` verschoben.
- Indexaufbau, Re-Scan, Status, Sitzungen, Backup, Restore und Reparatur nach
  `cli_index.py` verschoben.
- Klassischen Erklärungsbefehl nach `cli_help.py` verschoben.
- Gemeinsame Validierung, Ausgabe und Formatierung in `cli_common.py` zentralisiert.
- Parser und Handler liegen nun im selben Fachmodul.
- Bestehende Befehlsnamen und Parameter unverändert erhalten.

### Globale Wartungsregeln

- Versioniertes Regelmanifest `maintenance_rules.json` ergänzt.
- Verständliche Projektregeln in `MAINTENANCE_RULES.md` ergänzt.
- `CommandPolicy` für maschinenlesbare Lese- und Schreibwirkungen eingeführt.
- Originaldatei-Schreibzugriffe werden durch den CLI-Vertrag technisch abgewiesen.
- Einheitlicher Dispatch prüft Handler und Rückgabecodes.
- Größenlimit für `cli.py` auf 150 Zeilen festgelegt.
- Größenlimit für CLI-Fachmodule auf 500 Zeilen festgelegt.
- Shell-Auswertung, `eval`, `exec`, `os.system` und zyklische CLI-Importe verboten.

### Automatische Architekturprüfungen

- Alle öffentlichen Befehle besitzen registrierten Handler und Richtlinie.
- Zuständigkeit von Scan, Suche, Berichten, Index und Hilfe wird geprüft.
- Modulgrößen werden aus dem Regelmanifest geprüft.
- Verbotene Shell- und Ausführungsfunktionen werden über AST-Prüfung erkannt.
- Originaldatei-Schreibrichtlinien werden abgewiesen.
- Regelmanifest wird auf Version, Eindeutigkeit und Mindestumfang geprüft.

### Validiert

- Paketinstallation und Kompilierung unter Python 3.10 und 3.12 erfolgreich.
- 54 von 54 Tests unter beiden Python-Versionen erfolgreich.
- Tests mit `PYTHONWARNINGS=error` erfolgreich.
- Sämtliche bisherigen Scan-, Such-, Berichts-, Index-, Hilfe- und
  Startseitenprüfungen unverändert grün.
- Keine neue externe Laufzeitabhängigkeit.

## 0.7.0-alpha.1 – 2026-08-04

### Mehrschichtige Laienhilfe

- Soforthilfe direkt in der nummerierten Startseite.
- Detailhilfe über `?NUMMER`.
- Schritt-für-Schritt-Anleitung über `gNUMMER`.
- Feldbezogene Hilfe durch `?` bei Pfad-, Such- und Bestätigungsfragen.
- Kontextbezogene Fehlerhilfe nach fehlgeschlagenen Fachbefehlen.
- Eigenständiger Befehl `datenbanktool help`.
- Hilfestufen `quick`, `detail` und `guided`.
- Suche nach Hilfethemen über Alltagsbegriffe mit `--find`.
- JSON-Ausgabe des Hilfekatalogs.

### Codequalität

- Hilfedaten in `core/layered_help.py` zentralisiert.
- Startseitenlogik nach `core/guided_home.py` ausgelagert.
- Alter Importpfad `core/terminal_home.py` bleibt als schmale Kompatibilitätsschicht.
- Eigenständige Argumentauswertung in `help_command.py`.
- Keine Shell- oder Subprozessausführung durch die Hilfe.

### Validiert

- 48 von 48 Tests unter Python 3.10 und 3.12 erfolgreich.

## 0.6.0-alpha.1 – 2026-08-04

- Geführte Terminal-Startseite.
- Sichere Argumentlisten ohne Shell-Auswertung.
- Bestätigungsschutz für Indexaufbau, Re-Scan und Sicherung.
- Einheitlicher interaktiver Programmeinstieg.

## 0.5.0-alpha.1 – 2026-08-04

- Ordnerübersicht mit Platzfressern und Ampeln.
- Suchvorlagen.
- HTML-Tooltips und ausführliche Funktionsbeschreibungen.

## 0.4.0-alpha.1 – 2026-08-04

- Rein lesende SQLite-Suche mit Seiten und Filtern.
- Optionaler FTS5-Suchindex.
- Änderungsberichte als Terminal, JSON, CSV und HTML.

## 0.3.0-alpha.1 – 2026-08-04

- Inkrementeller Re-Scan, Prozesslock, Fortschrittsereignisse, Backup und Restore.

## 0.2.0-alpha.1 – 2026-08-04

- Versionierter SQLite-Index mit Migration und Wiederaufnahme.

## 0.1.0-alpha.1 – 2026-08-04

- Rein lesender Scanner, Klassifizierung, Namensprüfung und Duplikaterkennung.
