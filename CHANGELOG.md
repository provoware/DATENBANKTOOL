# Changelog

## 0.9.0-alpha.1 – 2026-08-04

### Rein lesender Ordnervergleich

- Neuer Befehl `datenbanktool index folder-compare DATENBANK`.
- Vergleicht rekursive Dateizahl und Gesamtgröße pro Ordner.
- Automatische Auswahl des neuesten passenden Scan-Paars.
- Explizite Auswahl über `--from-session-id` und `--to-session-id`.
- Nur abgeschlossene Sitzungen desselben Stammordners werden akzeptiert.
- Die Ausgangssitzung muss älter als die Zielsitzung sein.
- Zustände: gewachsen, kleiner geworden, neu, nicht mehr vorhanden,
  Dateizahl geändert und unverändert.
- Unveränderte Ordner werden standardmäßig ausgeblendet.
- Filter nach Zustand, Pfadtext, Mindeständerung und Ordnertiefe.
- Stabile Sortierung nach Pfad, Größenänderung, Prozentwert, Dateidifferenz
  oder aktueller Größe.
- Pagination mit begrenzter Seitengröße.
- Konfigurierbare Warnschwelle für starkes Wachstum.

### Ausgabe und Exporte

- Terminalausgabe mit vorheriger und neuer Größe, Dateizahl, Differenz und Prozentwert.
- Ampelfarbe immer zusammen mit Status und konkreter Begründung.
- Atomare JSON-, CSV- und HTML-Berichte.
- CSV mit UTF-8-BOM und Semikolon für LibreOffice Calc.
- Eigenständiger Offline-HTML-Bericht mit Escaping, Tooltips und ARIA-Beschriftungen.
- Vorhandene Berichte werden nur mit `--overwrite-report` ersetzt.
- `--no-terminal` ist nur zusammen mit mindestens einem Export zulässig.

### Laienhilfe

- Neuer Startseitenpunkt `10. Ordner vergleichen`.
- Detailhilfe über `?10`.
- Schritt-für-Schritt-Anleitung über `g10`.
- Eigenständige Hilfe über `datenbanktool help folder-compare`.
- Klassische Hilfe über `datenbanktool explain folder-compare`.
- Alltagssuche über Begriffe wie Wachstum, gewachsen, kleiner und Speicherverlauf.

### Sicherheit und Codequalität

- SQLite wird im Vergleich mit `mode=ro` und `PRAGMA query_only=ON` geöffnet.
- Die Datenbank bleibt bei reiner Anzeige bytegenau unverändert.
- Originaldateien werden nicht erneut gelesen oder verändert.
- Eigener modularer CLI-Baustein `cli_folder_compare.py`.
- Vergleichskern und Exportlogik sind getrennt testbar.
- Öffentlicher Befehl besitzt eine geprüfte `CommandPolicy`.
- Globale Größen-, Import- und Shell-Verbote bleiben erfüllt.

### Validiert

- Paketinstallation und Kompilierung unter Python 3.10 und 3.12 erfolgreich.
- 59 von 59 Tests unter beiden Python-Versionen erfolgreich.
- Tests jeweils mit `PYTHONWARNINGS=error`.
- Wachstum, Rückgang, neue, entfernte und unveränderte Ordner geprüft.
- Unterschiedliche Stammordner werden kontrolliert abgelehnt.
- JSON-, CSV- und HTML-Export geprüft.
- Startseite, mehrschichtige Hilfe und Architekturvertrag geprüft.
- Sämtliche bisherigen Scan-, Such-, Berichts-, Index-, Hilfe- und Startseitentests
  bleiben grün.

## 0.8.0-alpha.1 – 2026-08-04

- Große `cli.py` in klar abgegrenzte Fachmodule aufgeteilt.
- Öffentliche Befehle und Parameter unverändert erhalten.
- `CommandPolicy` für deklarierte Seiteneffekte eingeführt.
- Globale Wartungsregeln als Markdown und JSON angelegt.
- Architekturprüfungen für Größenlimits, Importgrenzen, Handler und Shell-Verbote.

## 0.7.0-alpha.1 – 2026-08-04

- Mehrschichtige Laienhilfe mit Sofort-, Detail-, Schritt-, Feld- und Fehlerhilfe.
- Eigenständiger Befehl `datenbanktool help`.
- Suche nach Hilfethemen über Alltagsbegriffe.

## 0.6.0-alpha.1 – 2026-08-04

- Geführte Terminal-Startseite.
- Sichere Argumentlisten ohne Shell-Auswertung.
- Bestätigungsschutz für Indexaufbau, Re-Scan und Sicherung.

## 0.5.0-alpha.1 – 2026-08-04

- Ordnerübersicht mit Platzfressern und Ampeln.
- Suchvorlagen.
- HTML-Tooltips und ausführliche Funktionsbeschreibungen.

## 0.4.0-alpha.1 – 2026-08-04

- Rein lesende SQLite-Suche mit Seiten und Filtern.
- Optionaler FTS5-Suchindex.
- Änderungsberichte als Terminal, JSON, CSV und HTML.

## 0.3.0-alpha.1 – 2026-08-04

- Inkrementeller Re-Scan, Prozesslock, Fortschrittsereignisse, Backup und Restore.

## 0.2.0-alpha.1 – 2026-08-04

- Versionierter SQLite-Index mit Migration und Wiederaufnahme.

## 0.1.0-alpha.1 – 2026-08-04

- Rein lesender Scanner, Klassifizierung, Namensprüfung und Duplikaterkennung.
