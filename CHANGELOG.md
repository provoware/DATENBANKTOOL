# Changelog

## 0.19.0-alpha.1 – 2026-08-05

### Vollständig lesende Wiederanlauf-Diagnose

- Neuer Befehl `datenbanktool index recovery`.
- Neue JSON-Ausgabe über `datenbanktool index recovery --json`.
- Jeder gespeicherte Wiederanlauf wird unabhängig gegen Quellordner, Indexdatei und neueste fortsetzbare SQLite-Sitzung geprüft.
- Terminal und JSON zeigen Prüfstatus, Ordner, Indexdatei, Sitzung, Zustand, Phase, bestätigte Dateizahl, UTC-Zeit und Startbarkeit.
- Gesamtzahlen für alle, startbare und nicht startbare Einträge werden ausgegeben.
- Die Diagnose startet keinen Scan und besitzt keinen Verwerfen- oder Löschhandler.
- Automatische Tests bestätigen, dass `resume-run.json` und die geprüfte Indexdatei bytegenau unverändert bleiben.
- Leere Wiederanlauflisten liefern eine erfolgreiche und stabile Terminal- sowie JSON-Ausgabe.

### Optionales Wiederherstellungsprotokoll

- `index backups restore` unterstützt neu `--restore-log PFAD`.
- Das Protokoll wird ausschließlich nach einer erfolgreich bestätigten Konfigurations-Wiederherstellung angelegt.
- Enthalten sind UTC-Zeiten, aktive Datei, ausgewählte Sicherung, Rückfallsicherung und drei eindeutig benannte SHA-256-Werte.
- Konfigurationsinhalte, Vorlagen, Antwortwerte, Kommandozeilenargumente und Geheimnisse werden nicht protokolliert.
- Veröffentlichung erfolgt atomar mit Dateimodus `0600`.
- Ein existierendes Ziel wird nicht überschrieben.
- Ohne `--restore-log` entsteht keine Protokolldatei.
- Es gibt keine automatische Benennung, Auswahl, Rotation oder Löschung.
- Scheitert nur das Protokoll, bleibt die bereits bestätigte Wiederherstellung bestehen; der Befehl meldet Teilfehlercode `1`.

### Architektur und Prüfung

- Neue Fachmodule `cli_recovery.py` und `core/restore_audit.py`.
- `cli.py` registriert nur den neuen Parser und bleibt unter der globalen Größenbegrenzung.
- Restore-Policy kennzeichnet die optionale Protokollschreibwirkung ausdrücklich als Berichtsschreibzugriff.
- Keine neue Laufzeitabhängigkeit, keine Shell-Auswertung und keine Originaldateioperation.
- Funktionsreferenz: 145 Tests unter Python 3.10 und 3.12; Quick- und Standardabnahme jeweils 11/11.

## 0.18.0-alpha.1 – 2026-08-05

- Geführte Konfigurations-Wiederherstellung mit rein lesendem Vergleich.
- Exakte Einzelauswahl, `--yes`, automatische geprüfte Rückfallsicherung und atomare Veröffentlichung.
- Vollständige Nachprüfung sowie automatischer Rückfall bei fehlgeschlagener Bestätigung.
- Keine automatische Auswahl, Rotation oder Löschung.

## 0.17.0-alpha.1 – 2026-08-05

- Begrenzte Wiederanlaufliste für zwölf verschiedene Indexdateien.
- Deduplizierung, Dateisperre, Einzelvalidierung und bewusstes Einzelverwerfen.
- Optionale geprüfte JSON-Sicherung vor dem Ersetzen oder Löschen von Vorlagen.

## 0.16.0-alpha.1 – 2026-08-05

- Geführter, gegen SQLite geprüfter Wiederanlauf.
- Sicherungsübersicht und kataloggebundene Einzellöschung.
- Zentrale Symlink-Sperre.

## 0.15.0-alpha.1 – 2026-08-05

- Prozessgrenze, Laufjournal und bereinigte Crashberichte.
- Zeit- und mengenbegrenztes Autosave sowie `--resume`.
- SQLite `WAL` mit `synchronous=FULL`.
- Dauerhafte atomare Dateifreigabe und Startklar-Prüfung.

## Frühere Entwicklungsstufen

- **0.14.x:** Registry-Konsolidierung und geführte Zeitreihen-Vorlagenverwaltung.
- **0.13.x:** Zeitreihen-Vorlagen, Trendgrenzen, Hilfen und Versionierungsvertrag.
- **0.12.x:** geführte Ordner-Zeitreihe und barrierefreie Offline-SVG-Trends.
- **0.11.x:** Ordner-Zeitreihe und vollständige Vergleichsexporte.
- **0.10.x:** Großbestandsabnahme und vollständige Ordnerexporte.
- **0.1–0.9:** Scanner, SQLite-Index, Re-Scan, Suche, Berichte, Startseite und Hilfe.
