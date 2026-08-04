# Entwicklerdokumentation

## Architekturstand 0.9.0-alpha.1

Die CLI bleibt modular. Der neue Ordnervergleich ist in drei klar getrennte Schichten
aufgeteilt:

1. `core/folder_compare.py` – reine Auswahl, Aggregation und Klassifizierung.
2. `core/folder_compare_exports.py` – atomare JSON-, CSV- und HTML-Ausgabe.
3. `cli_folder_compare.py` – Argumente, verständliche Terminaldarstellung und Dispatch.

Die bestehenden Schichten bleiben unverändert:

- `cli.py` – Zusammensetzung, Dispatch und zentrale Fehlergrenze,
- `cli_scan.py` – einmaliger Scan,
- `cli_search.py` – Suche und Suchvorlagen,
- `cli_reports.py` – bisherige Berichte,
- `cli_index.py` – Indexverwaltung,
- `cli_help.py` – klassischer Erklärungsbefehl,
- `cli_common.py` – gemeinsame Parser- und Ausgabehilfen,
- `cli_contract.py` – Handler- und Seiteneffektvertrag,
- `core/guided_home.py` – geführte Startseite,
- `core/layered_help.py` – mehrschichtiger Hilfekatalog.

## Öffentlicher Befehl

```text
datenbanktool index folder-compare DATENBANK
```

Optionale Sitzungswahl:

```text
--from-session-id ID
--to-session-id ID
```

Filter und Ausgabe:

```text
--type grown|shrunk|new|removed|changed|unchanged
--contains TEXT
--min-change-mib MIB
--max-depth N
--page N
--page-size N
--sort path|change|percent|files|current-size
--descending / --no-descending
--attention-growth-mib MIB
--json PFAD
--csv PFAD
--html PFAD
--overwrite-report
--no-terminal
```

## `core/folder_compare.py`

### Datenmodelle

`FolderComparisonFilter` enthält:

- gewünschte Zustände,
- Pfadtext,
- absolute Mindeständerung,
- maximale Tiefe,
- Seite und Seitengröße,
- Sortierung und Richtung,
- Warnschwelle für starkes Wachstum.

`FolderComparisonRow` enthält:

- Ordnerpfad und Tiefe,
- technischen und sichtbaren Zustand,
- Dateizahl vorher und nachher,
- Dateidifferenz,
- Größe vorher und nachher,
- absolute Größenänderung,
- prozentuale Größenänderung oder `None`,
- Ampelstufe, Status und Begründung.

`FolderComparisonPage` enthält:

- Datenbankpfad,
- Ausgangs- und Zielsitzung,
- Stammordner,
- Pagination,
- ungefilterte Zustandszähler,
- ausgewählte Zeilen.

Alle öffentlichen Datenmodelle sind unveränderliche Dataclasses mit Slots.

### Rein lesende Verbindung

Die Funktion `_readonly_connection()`:

1. normalisiert den Datenbankpfad,
2. verlangt eine vorhandene Datei,
3. öffnet SQLite über URI mit `mode=ro`,
4. aktiviert `PRAGMA query_only=ON`,
5. lehnt neuere unbekannte Schemaversionen ab,
6. verlangt Schema 3 für Sitzungsbeziehungen.

Der Vergleich führt kein `INSERT`, `UPDATE`, `DELETE`, `CREATE` oder `VACUUM` aus.

### Auswahl der Zielsitzung

Mit `--to-session-id` wird genau diese abgeschlossene Sitzung verwendet.

Ohne Angabe wird die neueste abgeschlossene Sitzung gewählt, die entweder:

- einen `parent_session_id` besitzt oder
- einen älteren abgeschlossenen Scan desselben Stammordners besitzt.

Dadurch wird nicht versehentlich ein einzelner isolierter Erstscan ausgewählt.

### Auswahl der Ausgangssitzung

Reihenfolge:

1. explizite `--from-session-id`,
2. direkter `parent_session_id` der Zielsitzung,
3. vorherige abgeschlossene Sitzung desselben Stammordners.

Danach gelten zwei harte Prüfungen:

- Ausgangs-ID muss kleiner als Ziel-ID sein,
- normalisierte Stammordner müssen übereinstimmen.

### Rekursive Aggregation

Für jede Datei einer Sitzung werden gespeichert:

- Gesamtdateizahl,
- Gesamtgröße in Byte.

Die Werte werden dem direkten Elternordner und allen Vorfahren bis `.` zugerechnet.
Ein Ordner ohne Dateien und ohne belegte Unterordner kann nicht entstehen, weil das
aktuelle Schema keine eigenständigen Verzeichniszeilen speichert.

### Klassifizierung

Reihenfolge der Zustände:

1. vorher 0 Dateien, nachher >0 → `new`,
2. vorher >0 Dateien, nachher 0 → `removed`,
3. positive Größendifferenz → `grown`,
4. negative Größendifferenz → `shrunk`,
5. gleiche Größe, andere Dateizahl → `changed`,
6. sonst → `unchanged`.

Neue Ordner erhalten `size_delta_percent=None`, da eine Division durch einen
Ausgangswert von null keinen sinnvollen Prozentwert liefert.

### Ampellogik

- `grown` oberhalb der Warnschwelle → Rot / Stark gewachsen,
- sonstiges `grown` → Gelb / Gewachsen,
- `new` → Gelb / Neu,
- `changed` → Gelb / Dateizahl geändert,
- `shrunk` → Grün / Kleiner geworden,
- `removed` → Grün / Nicht mehr vorhanden,
- `unchanged` → Grün / Unverändert.

Ampeln sind Darstellungsmetadaten. Die konkrete Begründung wird in jeder Ausgabe
zusätzlich verwendet.

### Filter und Sortierung

Ohne `change_types` werden unveränderte Ordner ausgeblendet. Sobald mindestens ein
Zustand angegeben ist, werden exakt diese Zustände verwendet.

`min_change_bytes` arbeitet mit dem Absolutbetrag. Ein Rückgang um 500 MiB erfüllt
damit dieselbe Mindestschwelle wie ein Wachstum um 500 MiB.

Stabile Sortierungen besitzen immer Pfad-Fallbacks. Die Seitengröße ist auf 200
begrenzt.

## `core/folder_compare_exports.py`

### Atomare Schreibweise

Alle Formate werden zuerst in eine Prozess-spezifische temporäre Datei geschrieben und
erst danach per `replace()` freigegeben. Bei Fehlern wird die temporäre Datei entfernt.
Vorhandene Ziele benötigen `overwrite=True`.

### JSON

- UTF-8,
- eingerückt,
- vollständige Seitenmetadaten,
- keine ANSI-Farben oder Bedienhinweise.

### CSV

- UTF-8 mit BOM,
- Semikolon als Trennzeichen,
- Rohwerte in Byte für verlässliche Berechnung,
- Status, Ampel und Begründung als getrennte Spalten.

### HTML

- vollständig eigenständig und offline,
- alle dynamischen Texte HTML-maskiert,
- responsive Standardtabelle,
- Farbklasse plus sichtbarer Status,
- `title`-Tooltip und `aria-label`,
- Scan-IDs und Stammordner im Kopf.

Die Exporte enthalten die Zeilen der übergebenen `FolderComparisonPage`, also die
aktuell gefilterte Seite.

## `cli_folder_compare.py`

Das Modul registriert Parser und Handler gemeinsam und erfüllt damit Regel G-002.

Die Richtlinie lautet:

```python
CommandPolicy("index.folder-compare", writes_reports=True)
```

`writes_original_files` und `writes_index` bleiben `False`.

Der Handler:

1. prüft `--no-terminal` gegen vorhandene Exportziele,
2. übersetzt MiB-Werte in Byte,
3. ruft den Vergleichskern auf,
4. gibt Sitzungsnummern und Zustandszähler aus,
5. rendert jede Zeile mit Ampel, Klartext und Differenzen,
6. erzeugt gewählte Berichte,
7. liefert Rückgabecode 0 bei Erfolg.

## Startseite und Hilfe

`core/guided_home.py` besitzt die neue Aktion:

```python
MenuAction("10", "folder-compare", "folder_compare")
```

Sie benötigt keine Bestätigung, da der direkte Vergleich rein lesend ist. Der Builder
übergibt nur eine sichere Argumentliste:

```text
index folder-compare DATENBANK
```

`core/layered_help.py` bietet:

- Soforthilfe in der Menüzeile,
- Detailhilfe über `?10`,
- geführte Hilfe über `g10`,
- Fehlerhilfe bei Rückgabecode ungleich null,
- direkte Hilfe über `datenbanktool help folder-compare`.

`core/help_system.py` hält zusätzlich den kompatiblen Befehl
`datenbanktool explain folder-compare` bereit.

## Automatische Prüfungen

`tests/test_folder_compare.py` prüft:

1. Wachstum,
2. Größenrückgang,
3. neue Ordner,
4. nicht mehr vorhandene Ordner,
5. unveränderte Ordner auf ausdrückliche Anforderung,
6. automatische Sitzungswahl,
7. explizite Sitzungswahl,
8. bytegenau unveränderte Datenbank,
9. Ablehnung unterschiedlicher Stammordner,
10. Terminalausgabe,
11. JSON-, CSV- und HTML-Export,
12. UTF-8-BOM des CSV-Exports,
13. Pflicht eines Exports bei `--no-terminal`,
14. Verbindung zu Startseite und mehrschichtiger Hilfe.

`tests/test_cli_architecture.py` prüft zusätzlich Handler, `CommandPolicy`,
Modulzuständigkeit, Größenlimits und Shell-Verbote.

Gesamtstand:

- 59 Tests unter Python 3.10,
- 59 Tests unter Python 3.12,
- `PYTHONWARNINGS=error`,
- vollständige Kompilierung von `src` und `tests`.

## Bekannte technische Grenzen

- Vergleich von genau zwei Sitzungen, keine Zeitreihe.
- Keine leeren Ordner ohne Dateieinträge.
- Rekursive Elternwerte überlappen Kindwerte bewusst.
- Export der aktuellen Seite, nicht automatisch aller gefilterten Treffer.
- Praktische Ressourcenmessung mit sehr großen Beständen steht noch aus.

## Nächster Entwicklungsblock

CSV-Export der normalen Ordnerübersicht mit denselben Filtern, stabiler Sortierung,
UTF-8-BOM, atomarem Schreiben und Überschreibschutz ergänzen.

## Sichere Zusatzverbesserung

Reproduzierbare Großbestands- und Laienabnahme vorbereiten, ohne automatische
Originaldateioperationen freizuschalten.

## Unverändert

`AGENTS.md` wird nicht verändert. Die globalen Wartungsregeln und das Verbot
automatischer Originaldatei-Schreibzugriffe bleiben vollständig wirksam.
