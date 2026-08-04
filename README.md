# DATENBANKTOOL

**Erledigt:** schreibgeschützte SQLite-Analyse, Tabellenübersicht, validierte Text-/JSON-Ausgabe und automatische Tests.

**Offen:** weitere Datenbanktreiber und eine grafische Oberfläche.

**Entwicklungsfortschritt:** **35 %** (stabiler SQLite-MVP).

**Mögliche Upgrades:** CSV-Export und optionale PostgreSQL-Anbindung; Details stehen im [Upgrade-Pool](UPGRADE_POOL.md).

Das DATENBANKTOOL zeigt Aufbau und Kerndaten einer lokalen SQLite-Datenbank, ohne sie zu verändern. Es benötigt Python 3.10 oder neuer und keine zusätzlichen Laufzeitpakete.

## Installation

```bash
python -m pip install -e .
```

## Verwendung

```bash
datenbanktool summary beispiel.sqlite
datenbanktool tables beispiel.sqlite
datenbanktool --json summary beispiel.sqlite
```

`summary` zeigt Dateigröße sowie die Anzahl der Tabellen und Spalten. `tables` zeigt die Spalten jeder selbst angelegten Tabelle. `--json` erzeugt maschinenlesbare Ausgaben; ein Eingabefehler endet mit Statuscode `2`.

## Entwicklung

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Die Version wird ausschließlich in `registry.json` gepflegt. Architektur und Qualitätsregeln beschreibt die [Entwicklerdokumentation](ENTWICKLERDOKU.md).
