# Changelog

## 0.16.0-alpha.1 – 2026-08-05

### Geführter Wiederanlauf

- Bestätigte `index build`- und `index rescan`-Befehle werden zusätzlich als eigener fortsetzbarer Scanstand gespeichert.
- Die Startseite prüft Wiederanlaufdatensatz, Ordner, Indexdatei, Scanart und SQLite-Sitzung nur lesend gegeneinander.
- Ein gültiger Wiederanlauf zeigt Art, Ordner, Indexdatei, Sitzung, Phase, Dateizahl und den vollständigen `--resume`-Befehl.
- Fortsetzung startet ausschließlich nach sichtbarer Ja/Nein-Bestätigung.
- Ablehnen, Abbrechen oder geschlossene Eingabe lässt den Wiederanlauf für später erhalten.
- Ein erfolgreicher Scan entfernt nur den internen Wiederanlaufhinweis; Laufjournal und Index bleiben erhalten.
- Veraltete Hinweise ohne fortsetzbare SQLite-Sitzung werden kontrolliert entfernt.
- Vollscan und inkrementeller Re-Scan besitzen getrennte geprüfte Wiederanlaufpfade.

### Sicherungsübersicht

- Neuer Befehl `index backups list` für Index- und Konfigurationssicherungen.
- Anzeige von Typ, Pfad, Größe, UTC-Zeitpunkt, verständlichem Alter, Status und technischer Begründung.
- SQLite-Sicherungen werden im Nur-Lese-Modus mit `quick_check` und Schemaversion geprüft.
- Konfigurationssicherungen werden auf gültiges JSON, Schemaversion und Vorlagenliste geprüft.
- Neuer Befehl `index backups delete` löscht genau eine katalogisierte Datei.
- Löschen benötigt vollständigen Pfad, exakten Dateinamen und `--yes`.
- Aktive Dateien, unbekannte Pfade und symbolische Verknüpfungen sind ausgeschlossen.
- Startseitenpunkt 7 bündelt Erstellen, Anzeigen und einzelne bestätigte Löschung.
- Keine automatische Rotation, Sammellöschung oder Löschung nach Alter.

### Zusätzliche Härtung

- Dauerhafte Dateioperationen folgen keine symbolischen Verknüpfungen mehr.
- Atomare Veröffentlichung verweigert Symlink-Ziele auch bei ausdrücklichem Überschreiben.
- Dauerhafte Einzellöschung prüft selbst auf normale Datei und bestätigt anschließend den Ordnerzustand mit `fsync`.
- Sortierung der Sicherungsübersicht ist eindeutig „neueste zuerst“.

### Prüfung

- Wiederanlauf für Vollscan und Re-Scan.
- Ablehnen und späteres Fortsetzen.
- Veralteter Wiederanlaufhinweis.
- Exakte sichtbare Argumentliste ohne Shell.
- Gültige, beschädigte und unbekannte Sicherungen.
- CLI-JSON-Ausgabe und tatsächliche Einzellöschung.
- Fehlendes `--yes`, falscher Name, aktive Datei und Symlink.
- Zentrale Symlink-Sperre für Schreiben und Löschen.

## 0.15.0-alpha.1 – 2026-08-05

- Zentrale Prozessgrenze, Laufjournal und bereinigte Crashberichte.
- Autosave spätestens nach fünf Sekunden oder 500 Einträgen.
- Wiederaufnahme über `--resume`.
- SQLite `WAL` mit `synchronous=FULL`.
- Gemeinsame dauerhafte Dateifreigabe mit Datei- und Ordner-`fsync`.
- Startklar-Prüfung `datenbanktool check`.
- Alltagssprache vor technischen Einzelheiten.

## Frühere Entwicklungsstufen

- **0.14.x:** Registry-Konsolidierung und geführte Zeitreihen-Vorlagenverwaltung.
- **0.13.x:** Zeitreihen-Vorlagen, Trendgrenzen, Hilfen und Versionierungsvertrag.
- **0.12.x:** geführte Ordner-Zeitreihe und barrierefreie Offline-SVG-Trends.
- **0.11.x:** Ordner-Zeitreihe und vollständige Vergleichsexporte.
- **0.10.x:** Großbestandsabnahme und vollständige Ordnerexporte.
- **0.1–0.9:** Scanner, SQLite-Index, Re-Scan, Suche, Berichte, Startseite, Hilfe und Ordnervergleich.
