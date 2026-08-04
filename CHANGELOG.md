# Changelog

## 0.10.0-alpha.1 – 2026-08-04

### Ordnerübersicht als CSV

- Neuer Parameter `--csv PFAD` für `datenbanktool index folders`.
- Neuer ausdrücklicher Schalter `--all-pages` für vollständige Exporte.
- Terminalanzeige bleibt auch bei vollständigem Export paginiert.
- Ausgabe nennt die tatsächliche Zahl vollständig exportierter Ordner.
- CSV mit UTF-8-BOM und Semikolon für LibreOffice Calc.
- Stabile Spalten für Ampel, Begründung, Ordner, Tiefe, direkte und rekursive
  Dateizahlen, direkte und rekursive Bytegrößen, Namenshinweise und Duplikate.
- Größte Platzfresser werden als getrennte Pfad-/Byte-Spalten ausgegeben.
- Atomare Dateifreigabe und Schutz vor stillem Überschreiben.
- JSON und HTML können ebenfalls mit `--all-pages` vollständig erzeugt werden.
- `--all-pages` ohne gewählten Bericht wird kontrolliert abgelehnt.

### Reproduzierbare Großbestandsabnahme

- Neuer Befehl `datenbanktool acceptance`.
- Profile `quick`, `standard` und `large` mit 600, 10.000 und 100.000 Dateien.
- Deterministische synthetische Dateigrößen über festen Zufallsstartwert.
- Testdateien mit verschiedenen Endungen, Leerzeichen, Umlauten und
  Namenshinweisen.
- Testdaten werden ausschließlich in einem neuen Arbeitsordner erzeugt.
- Vorhandene Arbeitsordner werden abgelehnt und niemals bereinigt.
- Messung von Gesamt- und Phasenlaufzeiten.
- Messung des Python-Spitzenspeichers mit `tracemalloc`.
- Zusätzliche Erfassung des Prozess-Maximal-RSS.
- Vorher-/Nachher-Manifest für Pfad, Dateigröße und Nanosekunden-Änderungszeit.
- Elf feste Kriterien für Vollständigkeit, Fehlerfreiheit, CSV, Datenunverändertheit,
  Laufzeit und Speicher.
- Rückgabecode 1 bei verfehltem fachlichem Abnahmekriterium.

### Abnahmeberichte

Jeder Lauf erzeugt:

- `acceptance-result.json`,
- `acceptance-report.md`,
- `NOVICE_ACCEPTANCE_CHECKLIST.md`,
- `ordneruebersicht.csv`.

Die Laien-Checkliste enthält Aufgaben, Zeitfelder, Verständlichkeitsbewertungen,
Sicherheitsfragen, Fehlerfall und klare Abnahmekriterien. Sie wird ausdrücklich als
`pending-real-person` gekennzeichnet, bis eine reale Testperson sie ausfüllt.

### GitHub Actions

- 66 von 66 Tests unter Python 3.10 und 3.12 erfolgreich.
- Tests jeweils mit `PYTHONWARNINGS=error`.
- Quick-Abnahme: 600 Dateien, 11/11 Kriterien, 1,086 Sekunden,
  1.326.097 Byte Python-Spitzenspeicher.
- Standard-Abnahme: 10.000 Dateien, 11/11 Kriterien, 17,781 Sekunden,
  13.394.783 Byte Python-Spitzenspeicher.
- Quick- und Standardberichte werden als getrennte Artefakte 14 Tage archiviert.
- Das `large`-Profil ist implementiert, aber bewusst nicht Teil jedes normalen CI-Laufs.

### Sicherheit und Architektur

- `CommandPolicy` unterscheidet synthetische Testdaten von Originaldateien.
- Neue globale Regel G-015 für strikt isolierte Testdaten.
- Eigene Module `core/folder_csv.py`, `core/acceptance.py` und
  `cli_acceptance.py`.
- Keine neue externe Laufzeitabhängigkeit.
- Keine Shell-Auswertung.
- Originaldatei-Schreibzugriffe bleiben gesperrt.
- Bestehende Befehle und Ausgabeformate bleiben kompatibel.

## 0.9.0-alpha.1 – 2026-08-04

### Rein lesender Ordnervergleich

- Neuer Befehl `datenbanktool index folder-compare DATENBANK`.
- Vergleich rekursiver Dateizahlen und Gesamtgrößen zwischen zwei abgeschlossenen
  Sitzungen desselben Stammordners.
- Zustände für Wachstum, Rückgang, neue, entfernte, geänderte und unveränderte Ordner.
- Filter, stabile Sortierung, Pagination und JSON-/CSV-/HTML-Berichte.
- Startseitenpunkt 10 und vollständige Laienhilfe.
- 59 Tests unter Python 3.10 und 3.12.

## 0.8.0-alpha.1 – 2026-08-04

- Große `cli.py` in klar abgegrenzte Fachmodule aufgeteilt.
- `CommandPolicy`, globale Wartungsregeln und Architekturprüfungen eingeführt.

## 0.7.0-alpha.1 – 2026-08-04

- Mehrschichtige Laienhilfe und eigenständiger Hilfebefehl.

## 0.6.0-alpha.1 – 2026-08-04

- Geführte Terminal-Startseite und sichere Argumentlisten.

## 0.5.0-alpha.1 – 2026-08-04

- Ordnerübersicht, Platzfresser, Ampeln und Suchvorlagen.

## 0.4.0-alpha.1 – 2026-08-04

- Rein lesende SQLite-Suche, optionales FTS5 und Änderungsberichte.

## 0.3.0-alpha.1 – 2026-08-04

- Inkrementeller Re-Scan, Prozesslock, Fortschritt, Backup und Restore.

## 0.2.0-alpha.1 – 2026-08-04

- Versionierter SQLite-Index mit Migration und Wiederaufnahme.

## 0.1.0-alpha.1 – 2026-08-04

- Rein lesender Scanner, Klassifizierung, Namensprüfung und Duplikaterkennung.
