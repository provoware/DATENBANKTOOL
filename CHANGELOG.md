# Changelog

## 0.12.0-alpha.1 – 2026-08-04

### Geführte Ordner-Zeitreihe

- Neuer Startseitenpunkt `11. Ordner-Zeitreihe`.
- Sicherer Dialog für Indexdatenbank, relativen Ordner, Scan-Grenzen, Zeitpunkte und
  optionalen Bericht.
- Feldhilfe über `?` für jede neue Eingabe.
- Detailhilfe über `?11`.
- Schritt-für-Schritt-Anleitung über `g11`.
- Eigenständiges Hilfethema `folder-timeline` im Hilfezentrum.
- Suche über Alltagsbegriffe wie Zeitreihe, Verlauf und Speicherentwicklung.
- Zahlenvalidierung für Scan-IDs und 2 bis 500 Zeitpunkte vor dem Start.
- Berichtsauswahl auf kein, JSON, CSV oder HTML begrenzt.
- Geplanter Befehl wird sichtbar und als Argumentliste ohne Shell gestartet.
- Zeitreihenspezifische Fehlerhilfe für fehlende Scans, unpassende Sitzungen,
  unsichere Pfade und vorhandene Berichtszielen.

### Barrierefreie Offline-Trendgrafiken

- Zwei lokale SVG-Liniendiagramme im HTML-Zeitreihenbericht:
  Größenverlauf und Dateizahlverlauf.
- Kein JavaScript und keine externen Ressourcen.
- `figure`, `figcaption`, SVG-`title`, SVG-`desc` und `aria-labelledby`.
- Sichtbare Achsen-, Scan- und Wertbeschriftungen.
- Jeder Datenpunkt ist fokussierbar und besitzt eine genaue zugängliche Beschreibung.
- Textliche Zusammenfassung von Minimum, Maximum und Nettoänderung.
- Vollständige Zeitreihenwertetabelle unter den Diagrammen.
- Bei langen Verläufen werden nur sichtbare Beschriftungen reduziert; Datenpunkte und
  Tabellenwerte bleiben vollständig.
- Responsive Darstellung und Fokusmarkierung ohne Animation oder Skript.

### Architektur und Sicherheit

- Neues Modul `core/folder_timeline_help.py` für den vollständigen Hilfetextvertrag.
- Neues Modul `core/folder_timeline_charts.py` für reine SVG-Erzeugung.
- `core/guided_home.py` um validierte Zeitreiheneingaben erweitert.
- `help_command.py` bindet das neue Hilfethema in Liste, Suche, JSON und alle
  Hilfestufen ein.
- `core/folder_timeline_exports.py` bleibt für atomare Formatausgabe zuständig.
- Keine neue Laufzeitabhängigkeit.
- Keine Shell-Auswertung, kein JavaScript und keine externen HTML-Ressourcen.
- SQLite und Originaldateien bleiben unverändert.
- `AGENTS.md` bleibt unverändert.

### Automatische Prüfung

- Gesamtumfang auf 77 Tests erweitert.
- Menüpunkt, sichere Argumentliste und alle geführten Eingaben geprüft.
- Detail-, Schritt-, Feld- und Fehlerhilfe geprüft.
- Hilfesuche nach Alltagsbegriffen geprüft.
- Zwei SVGs, Rollen, Titel, Beschreibungen und Tastaturpunkte geprüft.
- Fehlende Skripte und externe HTTP-/HTTPS-Ressourcen geprüft.
- Vollständige Tabelle unter den Diagrammen geprüft.
- 77/77 Tests unter Python 3.10 und Python 3.12 erfolgreich.
- Tests jeweils mit `PYTHONWARNINGS=error`.
- Quick-Abnahme: 600 Dateien, 11/11 Kriterien, 1,015 Sekunden,
  1.325.982 Byte Python-Spitzenspeicher.
- Standard-Abnahme: 10.000 Dateien, 11/11 Kriterien, 16,116 Sekunden,
  13.398.883 Byte Python-Spitzenspeicher.
- Quick-Artefakt: ID 8898514789,
  SHA-256 `72e26044b5d02b06c771f74c505b3719cc0cbf5219e8965d6dfb80e0e3b7955e`.
- Standard-Artefakt: ID 8898524811,
  SHA-256 `930f15a0d6e0c942a9dffe0f48e45715dd412db5d815b174b94cd37225ab2bab`.

## 0.11.0-alpha.1 – 2026-08-04

- Rein lesende Ordner-Zeitreihe über mehrere abgeschlossene Scans.
- Rekursive Dateizahl, Größe, Differenzen, Prozentwerte und Zustände.
- Atomare JSON-, Calc-CSV- und Offline-HTML-Berichte.
- Vollständiger Ordnervergleichsexport über `--all-pages`.
- 71 Tests unter Python 3.10 und Python 3.12.

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

- Rein lesende SQLite-Suche, optionale FTS5-Suche und Änderungsberichte.

## 0.3.0-alpha.1 – 2026-08-04

- Inkrementeller Re-Scan, Prozesslock, Fortschritt, Backup und Restore.

## 0.2.0-alpha.1 – 2026-08-04

- Versionierter SQLite-Index mit Migration und Wiederaufnahme.

## 0.1.0-alpha.1 – 2026-08-04

- Rein lesender Scanner, Klassifizierung, Namensprüfung und Duplikaterkennung.
