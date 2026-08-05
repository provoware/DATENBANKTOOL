# Changelog

## 0.15.0-alpha.1 – 2026-08-05

### Absturzsicherheit und Autosave

- Zentrale Prozessgrenze für unerwartete Ausnahmen ergänzt.
- Unerwartete Programmfehler enden kontrolliert mit Rückgabecode `70`.
- Tastaturabbruch endet mit `130` und markiert laufende Scans als unterbrochen.
- Lokales Laufjournal unter `$XDG_STATE_HOME/datenbanktool/last-run.json` ergänzt.
- Eindeutige Crashberichte mit Python-, Plattform-, Versions- und Tracebackdaten ergänzt.
- Werte hinter typischen Token-, Passwort-, Secret- und API-Key-Schaltern werden ausgeblendet.
- Scan-Autosave speichert standardmäßig spätestens nach fünf Sekunden oder 500 Einträgen.
- Vollscan und Änderungsprüfung können am letzten bestätigten Pfad mit `--resume` fortgesetzt werden.
- Sehr große Dateien werden nach einem Abbruch höchstens für den gerade laufenden Einzelhash erneut gelesen.

### Dauerhafte Schreibgrenze

- Neue gemeinsame Schreibschicht `core/durable_files.py`.
- Temporärdateien werden vollständig geschrieben und mit Datei-`fsync` bestätigt.
- Veröffentlichung erfolgt im selben Ordner über `os.replace`.
- Der Zielordner wird anschließend mit Verzeichnis-`fsync` bestätigt.
- Fehlgeschlagene Veröffentlichung hält die alte Zieldatei unverändert und entfernt die Temporärdatei.
- Such- und Zeitreihenvorlagen, gemeinsame JSON-Berichte, Ordnervergleich, Ordner-Zeitreihe, Sicherung und Wiederherstellung verwenden die gehärtete Grenze.
- Sicherungen werden vor Veröffentlichung mit SQLite `quick_check` geprüft.
- Wiederherstellung behält standardmäßig eine Rückfallsicherung.

### SQLite-Härtung

- Schreibende Indexverbindungen verwenden `WAL`, `synchronous=FULL` und `wal_autocheckpoint=1000`.
- Bestätigte Batches, Abschluss-, Abbruch- und Fehlerzustände werden dauerhaft committed.
- Ein vorübergehend blockierter passiver WAL-Checkpoint bricht einen bereits sicheren Commit nicht mehr ab.
- Python-3.10-Kompatibilitätsfehler im Versionstest behoben; kein `tomllib` aus Python 3.11 mehr erforderlich.

### Einfache Nutzeransprache

- Neue Startklar-Prüfung `datenbanktool check`.
- Optionaler Nur-Lese-Test einer Indexdatei über `--database`.
- Öffentliche Einstiegstexte nennen zuerst Alltagssprache, dann Auswirkung, nächsten Schritt und erst danach Fachdetails.
- Kontrollierte CLI-Fehler bestätigen ausdrücklich, dass Originaldateien nicht automatisch verändert wurden.
- Zahlen-, Pfad-, Sicherungs- und Vorlagenfehler wurden verständlicher formuliert.

### Automatische Prüfung

- Simulation einer fehlgeschlagenen atomaren Umschaltung.
- Prüfung unveränderter Altdatei und entfernten Temporärrests.
- Prüfung von Dateimodus `0600`.
- Crashbericht-, Geheimnis-Ausblendungs- und Rückgabecodeprüfung.
- Tastaturabbruch- und Laufjournalprüfung.
- Unterbrechungs- und Wiederaufnahmetest.
- SQLite-`FULL`- und Nur-Lese-Diagnosetest.
- Architekturbindung des neuen Diagnosebefehls.

## Frühere Entwicklungsstufen

- **0.14.0-alpha.1:** Registry-Konsolidierung und geführte Zeitreihen-Vorlagenverwaltung.
- **0.13.x:** Zeitreihen-Vorlagen, Trendgrenzen, Hilfen und Versionierungsvertrag.
- **0.12.x:** geführte Ordner-Zeitreihe und barrierefreie Offline-SVG-Trends.
- **0.11.x:** Ordner-Zeitreihe und vollständige Vergleichsexporte.
- **0.10.x:** Großbestandsabnahme und vollständige Ordnerexporte.
- **0.1–0.9:** Scanner, SQLite-Index, Re-Scan, Suche, Berichte, Startseite, Hilfe und Ordnervergleich.
