# Changelog

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
- Alter Importpfad `core/terminal_home.py` bleibt als schmale Kompatibilitätsschicht erhalten.
- Eigenständige Argumentauswertung in `help_command.py`.
- Keine Erweiterung der bereits großen `cli.py`.
- Keine Shell- oder Subprozessausführung durch die Hilfe.
- Neue Module halten die konfigurierte Zeilenlänge ein.

### Sicherheit

- Hilfe liest ausschließlich eingebaute Texte.
- Feldhilfe verändert keine Eingabedaten und keine Dateien.
- Fehlerhilfe führt keine automatische Reparatur aus.
- Schreibende Startseitenaktionen benötigen weiterhin eine Bestätigung.
- Originaldatei-Schreibfunktionen bleiben gesperrt.

### Validiert

- Paketinstallation und Kompilierung unter Python 3.10 und 3.12 erfolgreich.
- 48 von 48 Tests unter beiden Python-Versionen erfolgreich.
- Tests mit `PYTHONWARNINGS=error` erfolgreich.
- Bestehende Startseiten-, Scan-, Such-, Berichts-, Backup- und Restore-Tests unverändert grün.
- Detailhilfe startet keine Aktion.
- Geführte Hilfe zeigt vollständige Schritte.
- Feldhilfe wiederholt die ursprüngliche Frage kontrolliert.
- Alltagssuche findet passende Hilfethemen.
- Unbekannte Themen enden mit verständlichem Fehlercode 2.

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
