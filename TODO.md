# TODO

Stand: Version `0.15.0-alpha.1`

## In dieser Iteration erledigt

1. [x] Unerwartete Ausnahmen an einer zentralen Prozessgrenze kontrolliert abfangen.
2. [x] Laufjournal und eindeutige lokale Crashberichte ergänzen.
3. [x] Typische Zugangsdaten in Crashberichten automatisch ausblenden.
4. [x] Tastaturabbruch als fortsetzbare Unterbrechung speichern.
5. [x] Autosave auf spätestens fünf Sekunden oder 500 Einträge begrenzen.
6. [x] Vollscan und Änderungsprüfung nach Unterbrechung über `--resume` fortsetzen.
7. [x] SQLite auf `WAL` und `synchronous=FULL` härten.
8. [x] Blockierte passive WAL-Aufräumphase vom sicheren Commit entkoppeln.
9. [x] Gemeinsame dauerhafte Dateifreigabe mit Datei- und Ordner-`fsync` entwickeln.
10. [x] Konfigurationen, Berichte, Sicherung und Wiederherstellung an die gemeinsame Schreibgrenze anbinden.
11. [x] `datenbanktool check` für Start-, Schreib-, Laufjournal- und Indexprüfung ergänzen.
12. [x] Nutzertexte auf Alltagssprache zuerst und Fachbegriff danach umstellen.
13. [x] Ausfall-, Abbruch-, Wiederaufnahme-, Geheimnis- und Nur-Lese-Tests ergänzen.
14. [x] Python-3.10-Versionstest ohne Python-3.11-Sondermodul reparieren.
15. [x] Version und Pflichtdokumentation auf `0.15.0-alpha.1` synchronisieren.

## Offener Hauptpunkt

1. [ ] Reale Laienabnahme auf einem Kubuntu-Zielsystem durch eine unerfahrene Testperson durchführen. Dabei besonders prüfen: Verständnis von Autosave, `--resume`, Crashbericht, Startklar-Prüfung und technischen Zusätzen.

## Nicht blockierende Zielsystemprüfungen

- [ ] Rechner während eines großen synthetischen Scans kontrolliert neu starten und danach `check`, `status` und `--resume` dokumentiert ausführen.
- [ ] Verhalten bei fast vollem Datenträger mit ausschließlich synthetischen Testdaten prüfen.
- [ ] Unterschiedliche reale Dateisysteme und USB-Datenträger prüfen, ohne persönliche Quelldaten zu verändern.

## Direkt folgender technischer Entwicklungsschritt

**Geführter Wiederanlauf:** Nach erkanntem unterbrochenem Lauf auf der Startseite den passenden Prüfpfad, die Indexdatei und einen geprüften `--resume`-Befehl anzeigen. Ausführung erst nach sichtbarer Bestätigung.

## Alternative Verbesserung mit hohem Nutzen und geringem Risiko

**Automatische Sicherungsrotation:** Nur Index- und Konfigurationssicherungen nach Anzahl und Alter auflisten; Löschen weiterhin niemals automatisch, sondern ausschließlich nach Einzelprüfung und Bestätigung.
