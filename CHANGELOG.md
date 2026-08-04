# Changelog

Alle wichtigen Änderungen werden hier dokumentiert. Das Projekt verwendet semantische Versionierung.

## [0.1.0] - 2026-08-04

### Hinzugefügt

- Schreibgeschützte SQLite-Analyse mit den Befehlen `summary` und `tables`.
- Validierung von Pfaden, Dateitypen und SQLite-Signaturen.
- Menschenlesbare und JSON-Ausgabe mit definierten Exitcodes.
- Versionsregistry, Paketkonfiguration und automatische Tests.
## 0.13.0-alpha.1 – 2026-08-04

### Zeitreihen-Vorlagen

- Neuer Befehl `index timeline-presets` mit `list`, `show`, `save` und `delete`.
- Gespeichert werden nur Name, validierter relativer Ordner, Beschreibung und
  Zeitstempel; Datenbankpfade und Scan-Inhalte bleiben außerhalb der Vorlage.
- Standardpfad unter `$XDG_CONFIG_HOME/datenbanktool/timeline-presets.json`.
- Atomare JSON-Freigabe und Dateiberechtigung `0600`.
- Namen 1–64 Zeichen, Beschreibungen höchstens 240 Zeichen.
- Absolute Pfade und `..` werden abgelehnt.
- Vorhandene Namen werden ohne `--replace` nicht überschrieben.
- Löschen benötigt `--yes`.
- `folder-timeline` akzeptiert `--preset` und optional `--preset-file`.
- Positionaler Ordner und `--preset` schließen sich kontrolliert aus.

### Geführte Bedienung

- Startseitenpunkt 11 zeigt gespeicherte Vorlagen nummeriert mit Ordner und Beschreibung.
- Auswahl per Nummer oder exaktem Namen; leere Auswahl wechselt zur manuellen Eingabe.
- Gewählter Ordner bleibt vor dem Start sichtbar und kann bewusst angepasst werden.
- Neuer Startseitenpunkt 12 speichert Vorlagen erst nach sichtbarer Befehlsprüfung und
  ausdrücklicher Bestätigung.
- Feldhilfe für Vorlagenauswahl, Name, Beschreibung und Warnschwellen.
- Dezimalwerte akzeptieren Punkt oder deutsches Komma.
- Beschädigte Vorlagendateien blockieren nicht die manuelle Zeitreiheneingabe.

### Rein lesende Trendgrenzen

- Neue Optionen `--warn-size-growth-percent` und `--warn-file-growth-percent`.
- Vergleich erfolgt mit dem unmittelbar vorherigen sichtbaren Scan.
- Nur positives Wachstum kann eine Warnschwelle erreichen.
- Endliche Werte von 0 bis 1.000.000 Prozent werden akzeptiert.
- Bei vorherigem Wert null bleibt der Prozentwert leer.
- Treffer erscheinen als `ROT – Trendgrenze erreicht`.
- Jede Warnung nennt Messwert, konfigurierte Schwelle und konkrete Begründung.
- Klarer Zusatz: rein lesender Hinweis, keine Schadens- oder Löschentscheidung.
- Verlaufsklassifikation und Warnstatus bleiben getrennte Felder.

### Exporte und Barrierefreiheit

- JSON enthält konfigurierte Grenzen, Datei- und Größenprozente sowie Warnbegründungen.
- CSV enthält getrennte Spalten für Verlauf, Warnstatus, Rohwerte und Schwellen.
- HTML zeigt aktive Grenzen, Trefferzahl und vollständige Klartextbegründungen.
- SVG-Punkte mit Grenztreffer besitzen sichtbares Wort `Warnung`, eigene Klasse,
  Tastaturfokus, Titel und genaue ARIA-Beschreibung.
- HTML bleibt skriptfrei, vollständig lokal und ohne externe Ressourcen.

### Architektur und Prüfung

- Neue Module `core/timeline_presets.py` und `cli_timeline_presets.py`.
- `CommandPolicy` deklariert Konfigurationsschreibzugriffe ausdrücklich.
- CLI-Eigentümerschaft, Zeilengrenzen und Shell-Verbote erweitert geprüft.
- 86/86 Tests unter Python 3.10 und Python 3.12 erfolgreich.
- Tests mit `PYTHONWARNINGS=error` und erfolgreicher Kompilierung.
- Quick-Abnahme: 600 Dateien, 11/11, 1,129 s, 1.324.226 Byte Python-Peak.
- Standard-Abnahme: 10.000 Dateien, 11/11, 18,150 s,
  13.398.233 Byte Python-Peak.
- Quick-Artefakt: ID 8899780387,
  SHA-256 `c3678cdd50d235b9819475d6f1f6660e0367833c3a80f7faa5dff7ce990b0c1b`.
- Standard-Artefakt: ID 8899791444,
  SHA-256 `846ebbd02d213bc336800d330a8a2612e2a069e17e13362f0a27f5aa4ed7571d`.
- CLI-Startdatei von einem alten duplizierten SQLite-MVP-Vorspann bereinigt; `from __future__` steht wieder am Dateianfang.
- Large-Abnahme auf Zielhardware: 100.000 Dateien, 11/11, 218,722 s, 107.011.474 Byte Python-Peak, 309.166.080 Byte Prozess-RSS, Python 3.12.13, ext4 auf `/dev/vda`, KVM x86_64 mit 3 vCPU.

## 0.12.0-alpha.1 – 2026-08-04

- Geführter Startseitenpunkt für die Ordner-Zeitreihe.
- Detail-, Schritt-, Feld- und Fehlerhilfe.
- Zwei vollständig lokale barrierefreie SVG-Trendgrafiken.
- 77 Tests unter Python 3.10 und Python 3.12.

## 0.11.0-alpha.1 – 2026-08-04

- Rein lesende Ordner-Zeitreihe über mehrere abgeschlossene Scans.
- Atomare JSON-, Calc-CSV- und Offline-HTML-Berichte.
- Vollständiger Ordnervergleichsexport über `--all-pages`.

## 0.10.0-alpha.1 – 2026-08-04

- Ordnerübersicht als LibreOffice-kompatible CSV.
- Reproduzierbare Großbestandsabnahme mit quick, standard und large.

## 0.9.0-alpha.1 – 2026-08-04

- Rein lesender Ordnervergleich zwischen zwei Scans.

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
