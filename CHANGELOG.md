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
- Architekturvertrag prüft Handler, `CommandPolicy` und Modulzuständigkeit.
- SQLite-Zugriff ausschließlich über `mode=ro` und `PRAGMA query_only=ON`.
- Originaldatei-Schreibzugriffe bleiben gesperrt.
- Keine neue Laufzeitabhängigkeit und keine Shell-Auswertung.

### Finale Validierung

- Paket `datenbanktool-0.11.0a1` erfolgreich gebaut.
- 71 von 71 Tests unter Python 3.10 und Python 3.12 erfolgreich.
- Tests jeweils mit `PYTHONWARNINGS=error`.
- Quick-Abnahme: 600 Dateien, 11/11 Kriterien, 1,085 Sekunden,
  1.327.597 Byte Python-Spitzenspeicher.
- Standard-Abnahme: 10.000 Dateien, 11/11 Kriterien, 18,718 Sekunden,
  13.396.633 Byte Python-Spitzenspeicher.
- Quick-Artefakt: ID 8896682878,
  SHA-256 `ce9e7ca3ae074ffb9f64f22b5c6f9a3bb0d2306a7a8d16541c87633019df55e8`.
- Standard-Artefakt: ID 8896694104,
  SHA-256 `24410db0850c99f7a4fe9167906f35b34780463fa4ad802176b21e8109c31f17`.
- Beide Berichtssets werden 14 Tage aufbewahrt.
- Zeitreihenwerte, Datenbank-Unverändertheit und unsichere Pfade geprüft.
- JSON-, Calc-CSV- und Offline-HTML-Export geprüft.
- Vollständiger Vergleichsexport über mehrere Terminalseiten geprüft.
- Sämtliche bisherigen Funktionen bleiben grün.

## 0.10.0-alpha.1 – 2026-08-04

- Ordnerübersicht als LibreOffice-kompatible CSV.
- Vollständiger Ordnerexport über `--all-pages`.
- Reproduzierbare Großbestandsabnahme mit quick, standard und large.
- Laufzeit-, Speicher- und Quelldatenprüfung mit elf festen Kriterien.

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
