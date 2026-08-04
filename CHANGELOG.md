# Changelog

## 0.6.0-alpha.1 – 2026-08-04

### Hinzugefügt

- Geführte Terminal-Startseite über `datenbanktool start`.
- Automatischer Start der Menüansicht bei einem interaktiven Aufruf ohne Unterbefehl.
- Nummerierte Auswahl für Suche, Ordnerübersicht, Änderungen, Status, Indexaufbau, Re-Scan, Sicherung, Vorlagen und Hilfe.
- Schrittweise Abfrage benötigter Ordner-, Datenbank- und Suchwerte.
- Vorschau des vollständig geplanten Befehls vor der Ausführung.
- Zusätzliche Bestätigung vor Indexaufbau, Re-Scan und Sicherung.
- Ampel- und Klartextbeschreibung der Wirkung jeder Menüfunktion.
- Neues Hilfethema `datenbanktool explain start`.

### Codequalität

- Neuer schmaler Programmeinstieg `entrypoint.py` trennt Startlogik von der bestehenden CLI.
- Neues testbares Modul `terminal_home.py` enthält Menümodell und Eingabeabläufe.
- Vorhandene `cli.py` wurde nicht weiter vergrößert.
- Ausführung erfolgt als feste Argumentliste ohne Shell-Auswertung.
- Ein-/Ausgabeströme und Befehlsausführung sind für Tests austauschbar.
- Menüdefinition ist unveränderlich und prüft doppelte Auswahlnummern.
- Nicht-interaktive Aufrufe ohne Befehl beenden sich ohne Warteschleife.
- Pfade mit Leerzeichen bleiben sichere einzelne Argumente.

### Validiert

- Installierbares Paket `datenbanktool-0.6.0a1` erfolgreich gebaut.
- Kompilierung unter Python 3.10 und 3.12 erfolgreich.
- 39 von 39 automatisierten Tests unter beiden Python-Versionen erfolgreich.
- Testlauf mit `PYTHONWARNINGS=error` erfolgreich.
- Ungültige Menüauswahl, Abbruch, geschlossene Eingabe und Bestätigungsschutz geprüft.
- Sichere Argumentübergabe für Pfade und Suchtexte mit Leerzeichen geprüft.
- Nicht-interaktiver Leerstart ohne Blockierung geprüft.

## 0.5.0-alpha.1 – 2026-08-04

### Hinzugefügt

- Rein lesende Ordnerübersicht mit direkten und rekursiven Dateizahlen.
- Gesamter Speicherbedarf je Ordner.
- Liste der größten Platzfresser je Ordner.
- Ampelbewertung mit Grün, Gelb oder Rot und verständlicher Begründung.
- JSON-Export der Ordnerübersicht.
- Eigenständiger lokaler HTML-Bericht mit Hover-Tooltips und ARIA-Beschriftungen.
- Speicherbare Suchvorlagen mit Beschreibung, Filtern und Sortierung.
- Befehle zum Auflisten, Anzeigen, Ersetzen und bestätigten Löschen von Suchvorlagen.
- Start gespeicherter Vorlagen über `index search --preset`.
- Globaler Farbmodus `auto`, `always` oder `never`.
- Unterstützung der Umgebungsvariable `NO_COLOR`.
- Kontextabhängige Klartexthinweise in der Kommandozeile.
- Neuer Befehl `datenbanktool explain` für Zweck-, Wirkungs-, Schreib- und Risikobeschreibungen.

### Sicherheit und Bedienung

- Farben werden nie als einziges Signal verwendet.
- Jede Ampel enthält Farbnamen, Statuswort und Begründung.
- Normale Ordneranalyse bleibt vollständig lesend.
- Vorlagen werden atomar in einer separaten Benutzer-Konfigurationsdatei gespeichert.
- Vorlagenüberschreibung benötigt `--replace`.
- Vorlagenlöschung benötigt `--yes`.
- JSON-Ausgaben bleiben frei von ANSI-Farbcodes.
- Terminal-Hinweise können mit `--no-hints` deaktiviert werden.

### Validiert

- Installation und Kompilierung unter Python 3.10 und 3.12 erfolgreich.
- 31 von 31 automatisierten Tests erfolgreich.
- Testlauf mit `PYTHONWARNINGS=error` erfolgreich.
- Ordneraggregation einschließlich Unterordnern geprüft.
- Größte-Dateien-Sortierung geprüft.
- Ampeltexte und Farbabschaltung geprüft.
- HTML-Tooltips und ARIA-Beschriftungen geprüft.
- Vorlagen speichern, laden, ersetzen und löschen geprüft.
- Suche über gespeicherte Vorlage geprüft.
- JSON- und HTML-Ordnerberichte geprüft.

## 0.4.0-alpha.1 – 2026-08-04

- Rein lesende SQLite-Suche mit Seiten, festen Sortierungen und kombinierbaren Filtern.
- Optionaler FTS5-Suchindex.
- Änderungsansicht im Terminal sowie JSON-, CSV- und HTML-Berichte.

## 0.3.0-alpha.1 – 2026-08-04

- Inkrementeller Re-Scan, Prozesslock, Fortschrittsereignisse, Sitzungsverwaltung, Backup und Restore.

## 0.2.0-alpha.1 – 2026-08-04

- Versionierter SQLite-Index mit Batch-Import, Wiederaufnahme, Migration und Reparaturmodus.

## 0.1.0-alpha.1 – 2026-08-04

- Rein lesender Scanner, Dateiklassifizierung, Namensprüfung und exakte Duplikaterkennung.
