# Changelog

## 0.18.0-alpha.1 – 2026-08-05

### Geführte Konfigurations-Wiederherstellung

- Neuer rein lesender Befehl `index backups compare` für genau eine katalogisierte Konfigurationssicherung.
- Vergleich ordnet die Sicherung eindeutig der aktiven Such- oder Zeitreihen-Konfiguration zu.
- Terminal und JSON zeigen Vorlagen, die hinzukämen, entfernt, ersetzt oder unverändert blieben.
- Sicherung und aktive Datei erhalten getrennte SHA-256-Nachweise.
- Neuer Befehl `index backups restore` stellt genau eine grün geprüfte Konfigurationssicherung wieder her.
- Wiederherstellung verlangt den exakten Sicherungsdateinamen und `--yes`.
- Vor dem Überschreiben wird zwingend eine neue geprüfte Rückfallsicherung der aktiven Datei erstellt.
- Sicherung und aktive Datei werden unmittelbar vor der Mutation erneut gegen die Vergleichsprüfsummen kontrolliert.
- Veröffentlichung erfolgt atomar mit Dateimodus `0600`.
- Nach der Wiederherstellung werden Bytes, SHA-256 und das vollständige Such- oder Zeitreihen-Schema erneut validiert.
- Bei fehlgeschlagener Nachprüfung wird automatisch die neue Rückfallsicherung zurückgespielt und kontrolliert.
- Ausgewählte Sicherung und Rückfallsicherung bleiben erhalten.
- Keine automatische Auswahl, Rotation, Alterslöschung oder Sammellöschung.

### Geführte Startseite

- Menüpunkt 7 enthält nun die Aktion `wiederherstellen`.
- Angezeigt werden ausschließlich erkannte Konfigurationssicherungen.
- Vor der Bestätigung erscheint ein Nur-Lese-Vergleich mit aktiver Datei und allen Vorlagenänderungen.
- Bereits identische Dateien werden nicht überschrieben.
- Der Sicherungsname muss exakt wiederholt werden.
- Erst danach wird der vollständige Argumentlistenbefehl sichtbar bestätigt.

### Härtung und Prüfung

- Indexsicherungen, beschädigte JSON-Dateien, unbekannte Pfade und Symlinks werden abgelehnt.
- Fehlende aktive Konfigurationen führen zu keiner Neuanlage oder Überschreibung.
- Gleichnamige Vorlagen innerhalb einer Datei werden als uneindeutig abgelehnt.
- Tests simulieren eine fehlgeschlagene Nachprüfung und bestätigen den automatischen Rückfall.
- CLI-Parser, Handler, Policies, Modulgrenzen und Shellverbot wurden erweitert.
- Funktionsreferenz: 139 Tests unter Python 3.10 und 3.12; Quick- und Standardabnahme jeweils 11/11.

## 0.17.0-alpha.1 – 2026-08-05

- Begrenzte Wiederanlaufliste für zwölf verschiedene Indexdateien.
- Deduplizierung, Dateisperre, Einzelvalidierung und bewusstes Einzelverwerfen.
- Optionale geprüfte JSON-Sicherung vor dem Ersetzen oder Löschen von Vorlagen.
- Keine automatische Rotation oder Löschung.

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
