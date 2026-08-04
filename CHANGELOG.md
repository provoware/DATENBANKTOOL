# Changelog

## 0.11.0-alpha.1 – 2026-08-04

### Rein lesende Ordner-Zeitreihe

- Neuer Befehl `datenbanktool index folder-timeline DATENBANK [ORDNER]`.
- Chronologische Auswertung mehrerer abgeschlossener Scans desselben Stammordners.
- Rekursive Dateizahl und Gesamtgröße pro Zeitpunkt.
- Datei- und Größendifferenz zum jeweils vorherigen Scan.
- Prozentuale Größenänderung mit sauberem Null-Ausgangswert.
- Zustände: Ausgangswert, gewachsen, kleiner geworden, neu, entfernt,
  Dateizahl geändert und unverändert.
- Relative Pfadvalidierung; absolute Pfade und `..` werden abgelehnt.
- Auswahl über `--from-session-id`, `--to-session-id` und `--limit`.
- Transparente Kennzeichnung, wenn ältere Zeitpunkte durch das Limit ausgeblendet sind.
- Mindestens zwei abgeschlossene Scans werden verlangt.

### Zeitreihenberichte

- Atomare JSON-, CSV- und HTML-Berichte.
- CSV mit UTF-8-BOM und Semikolon für LibreOffice Calc.
- HTML vollständig offline mit Klartext, Tooltips und ARIA-Beschriftungen.
- Kein stilles Überschreiben vorhandener Berichte.
- Maschinenlesbare Felder für Scan-ID, Zeitpunkt, Modus, Dateien, Größen,
  Differenzen, Prozentwert, Status und Begründung.

### Vollständiger Ordnervergleichsexport

- Neuer Schalter `--all-pages` für `index folder-compare`.
- JSON, CSV und HTML können sämtliche gefilterten Vergleichszeilen enthalten.
- Terminalausgabe bleibt paginiert.
- Vollständige Ergebnismenge wird genau einmal berechnet.
- `paginate_folder_comparison()` schneidet daraus die sichtbare Terminalseite.
- `--all-pages` ohne Exportziel wird kontrolliert abgelehnt.
- Bestehendes Seitenverhalten ohne Schalter bleibt kompatibel.

### Hilfe, Sicherheit und Architektur

- Klassisches Hilfethema `folder-timeline` ergänzt.
- Vergleichshilfe erklärt den vollständigen Export.
- Neue Fachmodule `core/folder_timeline.py`, `core/folder_timeline_exports.py`
  und `cli_folder_timeline.py`.
- SQLite-Zugriff ausschließlich über `mode=ro` und `PRAGMA query_only=ON`.
- Originaldatei-Schreibzugriffe bleiben gesperrt.
- Keine neue Laufzeitabhängigkeit und keine Shell-Auswertung.

### Validiert

- 71 von 71 Tests unter Python 3.10 erfolgreich.
- Python 3.12, Quick- und Standardabnahme im finalen Versionslauf erneut geprüft.
- Zeitreihenwerte, Datenbank-Unverändertheit und unsichere Pfade geprüft.
- JSON-, Calc-CSV- und Offline-HTML-Export geprüft.
- Vollständiger Vergleichsexport über mehrere Terminalseiten geprüft.
- Sämtliche bisherigen Funktionen bleiben grün.

## 0.10.0-alpha.1 – 2026-08-04

### Ordnerübersicht als CSV

- Neuer Parameter `--csv PFAD` für `datenbanktool index folders`.
- Neuer ausdrücklicher Schalter `--all-pages` für vollständige Exporte.
- Terminalanzeige bleibt auch bei vollständigem Export paginiert.
- CSV mit UTF-8-BOM und Semikolon für LibreOffice Calc.
- Atomare Dateifreigabe und Schutz vor stillem Überschreiben.

### Reproduzierbare Großbestandsabnahme

- Neuer Befehl `datenbanktool acceptance`.
- Profile `quick`, `standard` und `large` mit 600, 10.000 und 100.000 Dateien.
- Laufzeit-, Speicher- und Quelldatenprüfung mit elf festen Kriterien.
- JSON-, Markdown-, CSV- und Laien-Checklistenberichte.
- Quick- und Standardprofile als GitHub-Actions-Artefakte archiviert.

## 0.9.0-alpha.1 – 2026-08-04

- Rein lesender Ordnervergleich zwischen zwei abgeschlossenen Scans.
- Filter, stabile Sortierung, Pagination und JSON-/CSV-/HTML-Berichte.

## 0.8.0-alpha.1 – 2026-08-04

- Modulare CLI-Fachmodule, `CommandPolicy` und globale Architekturregeln.

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
