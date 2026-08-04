# Changelog

Alle wesentlichen Projektänderungen werden in dieser Datei dokumentiert.

## 0.1.0-alpha.1 – 2026-08-04

### Hinzugefügt

- Python-Projektgrundlage mit CLI-Einstiegspunkt.
- Rein lesender Scanner für große Verzeichnisbäume.
- Dateiklassifizierung für Medien, Texte, Archive, Code und Dokumente.
- Nicht destruktive Prüfung riskanter Dateinamen.
- Kennzeichnung großer Dateien.
- Optionale exakte Duplikaterkennung mit Größen-Vorfilter und SHA-256.
- Atomare JSON-Berichtsausgabe ohne stilles Überschreiben.
- Projekt- und Sicherheitsregister.
- Basis-Regressionsprüfungen.
- Ausführliche README, Roadmap, Analyse, Schwachstellen- und Entwicklerdokumentation.

### Sicherheitsentscheidungen

- Schreibende Dateioperationen sind nicht implementiert und im Register gesperrt.
- Symbolischen Verzeichnissen wird standardmäßig nicht gefolgt.
- Hashing wird nur ausdrücklich aktiviert.
- Fehler einzelner Dateien werden protokolliert, statt den gesamten Scan unkontrolliert zu beenden.

### Unverändert

- `AGENTS.md` wurde in dieser Iteration nicht verändert.
