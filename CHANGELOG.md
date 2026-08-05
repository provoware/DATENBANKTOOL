# Changelog

## 0.20.0-alpha.1 – 2026-08-05

### Wiederherstellungsprotokoll-Prüfbefehl

- Neuer Befehl `datenbanktool index backups verify-log PROTOKOLL`.
- Maschinenlesbare Ausgabe über `--json`.
- Protokolldatei wird ausschließlich über den ausdrücklich angegebenen Pfad geprüft.
- Symlink-Protokolle werden abgelehnt und nicht verfolgt.
- Festes Schema mit exakt neun obersten Feldern wird validiert.
- Unterstützt werden ausschließlich Schema `1` und Ereignis `configuration_restore`.
- `configuration_kind` muss `search` oder `timeline` sein.
- Beide Zeitfelder müssen gültige UTC-Zeiten sein; die Protokollzeit darf nicht vor dem Restore-Abschluss liegen.
- Genau drei unterschiedliche absolute Pfade sind erforderlich.
- Genau drei benannte, kleingeschriebene SHA-256-Werte mit jeweils 64 Hexzeichen sind erforderlich.
- Fehlende oder zusätzliche Felder werden abgelehnt.

### Rein lesender Dateinachweis

- Aktive Datei, ausgewählte Sicherung und Rückfallsicherung werden mit `O_NOFOLLOW` nur lesend geöffnet.
- Jede vorhandene normale Datei wird gestreamt und per SHA-256 mit dem protokollierten Wert verglichen.
- Übereinstimmung, fehlende Datei, Hashabweichung, Symlink und nicht sicher lesbarer Pfad werden getrennt dargestellt.
- Grün wird nur ausgegeben, wenn alle drei Dateien vorhanden sind und übereinstimmen.
- Gelb kennzeichnet ein gültiges Protokoll mit mindestens einer fehlenden Datei.
- Rot kennzeichnet Hashabweichung, Symlink, falschen Dateityp oder Lesefehler.
- Rückgabecode `0` bedeutet vollständige Bestätigung, `1` einen unvollständigen oder abweichenden Dateinachweis und `2` ein ungültiges Protokoll.
- Der Befehl startet keine Wiederherstellung und verändert oder löscht keine geprüfte Datei.

### Architektur und Prüfung

- `core/restore_audit.py` enthält Schema- und Dateiprüfung zusammen mit dem bestehenden Schreibvertrag.
- Neues CLI-Fachmodul `cli_restore_audit.py` hält Parser und Terminal-/JSON-Darstellung getrennt von der Sicherungsverwaltung.
- `CommandPolicy("index.backups.verify-log")` besitzt keine Schreibwirkung.
- Keine neue Laufzeitabhängigkeit und keine Shell-Auswertung.
- 151 Tests unter Python 3.10 und 3.12; Quick- und Standardabnahme jeweils 11/11.

## 0.19.0-alpha.1 – 2026-08-05

- Vollständig lesende Terminal- und JSON-Diagnose aller gespeicherten Wiederanläufe.
- Optionales inhaltsfreies Wiederherstellungsprotokoll nach erfolgreichem Restore.
- Atomare Protokollveröffentlichung mit Modus `0600`, ohne Überschreiben, Rotation oder Löschung.

## 0.18.0-alpha.1 – 2026-08-05

- Geführte Konfigurations-Wiederherstellung mit rein lesendem Vergleich.
- Exakte Einzelauswahl, `--yes`, automatische Rückfallsicherung und automatischer Rückfall.

## 0.17.0-alpha.1 – 2026-08-05

- Begrenzte Wiederanlaufliste für zwölf verschiedene Indexdateien.
- Optionale geprüfte JSON-Sicherung vor Vorlagenänderungen.

## 0.16.0-alpha.1 – 2026-08-05

- Geführter, gegen SQLite geprüfter Wiederanlauf.
- Sicherungsübersicht, kataloggebundene Einzellöschung und zentrale Symlink-Sperre.

## 0.15.0-alpha.1 – 2026-08-05

- Prozessgrenze, Laufjournal, Crashberichte, Autosave und `--resume`.
- SQLite `WAL` mit `synchronous=FULL` und dauerhafte atomare Dateifreigabe.

## Frühere Entwicklungsstufen

- **0.14.x:** Registry-Konsolidierung und geführte Zeitreihen-Vorlagenverwaltung.
- **0.13.x:** Zeitreihen-Vorlagen, Trendgrenzen, Hilfen und Versionierungsvertrag.
- **0.12.x:** geführte Ordner-Zeitreihe und barrierefreie Offline-SVG-Trends.
- **0.11.x:** Ordner-Zeitreihe und vollständige Vergleichsexporte.
- **0.10.x:** Großbestandsabnahme und vollständige Ordnerexporte.
- **0.1–0.9:** Scanner, SQLite-Index, Re-Scan, Suche, Berichte, Startseite und Hilfe.
