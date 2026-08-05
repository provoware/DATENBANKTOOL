# Changelog

## 0.17.0-alpha.1 – 2026-08-05

### Mehrere unabhängige Wiederanläufe

- `resume-run.json` wurde von einem Einzelstand auf Schema 2 mit begrenzter Eintragsliste migriert.
- Bis zu zwölf verschiedene Indexdateien können gleichzeitig einen Wiederanlaufhinweis besitzen.
- Dieselbe normalisierte Indexdatei wird nur einmal geführt; ein neuerer Lauf aktualisiert ihren Eintrag.
- Dateisperre schützt paralleles Lesen und Schreiben der Wiederanlaufliste.
- Jeder Eintrag wird getrennt gegen Ordner, Indexdatei, Scanart, Stammordner und SQLite-Sitzung validiert.
- Die Startseite zeigt alle Einträge mit Ordner, Indexdatei und verständlichem Prüfstatus.
- Ein auswählbarer Eintrag kann einzeln fortgesetzt, erhalten oder bewusst verworfen werden.
- Nicht mehr verfügbare Einträge bleiben sichtbar, sind aber nicht startbar.
- Erfolgreiche Scans entfernen ausschließlich den eigenen Eintrag.
- Begrenzung oder Verwerfen verändert keine Index- oder Originaldatei.

### Geprüfte Konfigurationssicherungen vor Änderungen

- Neuer gemeinsamer Sicherungsvertrag für Such- und Zeitreihen-Vorlagen.
- `--backup-before-change` ist bei bewusstem Ersetzen und Löschen verfügbar.
- Die geführte Startseite fragt vor diesen Änderungen optional nach einer Sicherung.
- Quelle wird auf normale Datei, Symlinkfreiheit, UTF-8-JSON, Objektstruktur, `schema_version` und `presets`-Liste geprüft.
- Sicherungen erhalten UTC-Zeitstempel, Prozesskennung und Dateimodus `0600`.
- Inhalt, Schemaversion, Vorlagenzahl und SHA-256 werden nach dem Schreiben erneut geprüft.
- Eine fehlgeschlagene Sicherung verhindert die nachfolgende Vorlagenänderung.
- Ohne ausdrückliche Option wird keine Sicherung erzeugt.
- Es gibt keine automatische Rotation, Alterslöschung oder Sammellöschung.
- Neue Sicherungen erscheinen in der vorhandenen Sicherungsübersicht.

### Architektur und Prüfung

- Gemeinsame CLI-Hilfe für Vorlagenänderungen verhindert doppelte Sicherungslogik.
- `cli_search.py` bleibt wieder unter der verbindlichen 500-Zeilen-Grenze.
- Kompatibilitätsschicht enthält keine zweite Implementierung.
- Tests decken zwei unabhängige Indexdateien, Deduplizierung, Listenlimit, Einzelverwerfen und nicht startbare Einträge ab.
- Tests decken Suchvorlagen-Ersetzen, Zeitreihen-Vorlagen-Löschen, optionales Auslassen, mehrere erhaltene Sicherungen, beschädigtes JSON und Sicherungskatalog ab.
- Funktionsreferenz: 130 Tests unter Python 3.10 und 3.12; Quick- und Standardabnahme jeweils 11/11.

## 0.16.0-alpha.1 – 2026-08-05

- Geführter, gegen SQLite geprüfter Wiederanlauf eines unterbrochenen Vollscans oder Re-Scans.
- Sicherungsübersicht für Index- und Konfigurationssicherungen.
- Kataloggebundene, einzeln bestätigte Sicherungslöschung.
- Zentrale Symlink-Sperre für dauerhafte Schreib- und Löschvorgänge.

## 0.15.0-alpha.1 – 2026-08-05

- Zentrale Prozessgrenze, Laufjournal und bereinigte Crashberichte.
- Autosave spätestens nach fünf Sekunden oder 500 Einträgen.
- Wiederaufnahme über `--resume`.
- SQLite `WAL` mit `synchronous=FULL`.
- Gemeinsame dauerhafte Dateifreigabe mit Datei- und Ordner-`fsync`.
- Startklar-Prüfung `datenbanktool check`.

## Frühere Entwicklungsstufen

- **0.14.x:** Registry-Konsolidierung und geführte Zeitreihen-Vorlagenverwaltung.
- **0.13.x:** Zeitreihen-Vorlagen, Trendgrenzen, Hilfen und Versionierungsvertrag.
- **0.12.x:** geführte Ordner-Zeitreihe und barrierefreie Offline-SVG-Trends.
- **0.11.x:** Ordner-Zeitreihe und vollständige Vergleichsexporte.
- **0.10.x:** Großbestandsabnahme und vollständige Ordnerexporte.
- **0.1–0.9:** Scanner, SQLite-Index, Re-Scan, Suche, Berichte, Startseite und Hilfe.
