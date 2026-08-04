# Globale Wartungs- und Entwicklungsregeln

Diese Regeln gelten projektweit. Die maschinenlesbare Fassung steht in
`maintenance_rules.json`; Architekturtests prüfen die wichtigsten Grenzen automatisch.

## 1. Öffentliche Bedienung bleibt stabil

Bestehende Befehlsnamen, Parameter, Rückgabecodes und JSON-Felder werden nicht
unbemerkt verändert. Notwendige Änderungen erhalten eine versionierte Migration,
Changelog-Eintrag und Kompatibilitätstest.

## 2. Ein Fachbereich pro Modul

Parser und Ausführung einer Funktion liegen im selben Fachmodul:

- `cli_scan.py`: einmalige Scans,
- `cli_search.py`: Suche und Suchvorlagen,
- `cli_reports.py`: Ordner-, Änderungs- und Dateiberichte,
- `cli_index.py`: Indexaufbau, Re-Scan, Status, Sitzungen, Sicherung und Reparatur,
- `cli_help.py`: klassische Funktionsbeschreibung,
- `cli.py`: nur Zusammensetzung, Dispatch und zentrale Fehlergrenze.

`cli.py` darf keine Fachlogik zurückerhalten.

## 3. Abhängigkeiten zeigen nur nach innen

CLI-Fachmodule dürfen `cli_common.py`, `cli_contract.py` und Core-Module importieren.
Sie importieren niemals `cli.py` und erzeugen keine zyklischen Abhängigkeiten.

## 4. Jede Wirkung wird deklariert

Jeder Parser wird über `bind_handler()` mit einer `CommandPolicy` verbunden. Darin
steht, ob Originaldateien gelesen, Indexdaten, Berichte, Sicherungen oder
Konfigurationen geschrieben werden.

## 5. Originaldateien bleiben geschützt

Schreibzugriffe auf gescannte Originaldateien sind global gesperrt, bis ein eigener,
versionierter Sicherheitsvertrag mit Vorschau, Journal, Rückgängig-Funktion,
Quarantäne und Tests beschlossen wurde.

## 6. Schreibvorgänge sind atomar und ausdrücklich

Ersetzbare Dateien werden zuerst temporär geschrieben und erst nach erfolgreicher
Prüfung atomar freigegeben. Vorhandene Ziele werden ohne ausdrückliche Option nicht
überschrieben.

## 7. Keine Shell-Auswertung

CLI-Fachmodule verwenden weder `shell=True`, `os.system`, `eval` noch `exec`.
Nutzereingaben bleiben strukturierte Argumente.

## 8. Rückgabecodes sind einheitlich

- `0`: erfolgreich,
- `1`: fachlich abgeschlossen, aber unvollständig oder mit erkannten Problemen,
- `2`: kontrollierter Eingabe-, Datei-, SQLite- oder Sicherheitsfehler.

Handler liefern immer `int`.

## 9. Menschen- und Maschinenformate bleiben getrennt

JSON, CSV und andere Maschinenformate enthalten keine ANSI-Farben, Tooltips oder
Bedienhinweise. Farben ergänzen ausschließlich sichtbaren Klartext.

## 10. Größenlimits verhindern neue Monolithen

- `cli.py`: höchstens 150 Zeilen,
- jedes `cli_*.py`-Fachmodul: höchstens 500 Zeilen.

Wird ein Limit erreicht, wird vor der nächsten Funktion weiter aufgeteilt.

## 11. Jede Änderung erhält vollständige Prüfungen

Neue oder verschobene Funktionen benötigen mindestens Syntax-, Parser-, Handler-,
Fehler-, Sicherheits- und Rückwärtskompatibilitätstests. GitHub Actions prüft alle
unterstützten Python-Versionen mit Warnungen als Fehler.

## 12. Dokumentation und Registry bleiben synchron

README, Changelog, TODO, Upgrade-Pool, Schwachstellenanalyse, Analyse-Punkte,
Entwicklerdokumentation, Projektregister und diese Regeln werden am Ende jeder
Iteration gemeinsam geprüft.

## 13. Abhängigkeiten bleiben minimal

Neue Laufzeitabhängigkeiten benötigen eine dokumentierte Begründung, ihre
Offline-Auswirkung und eine geprüfte Alternative. Der aktuelle Zielwert bleibt null
externe Laufzeitabhängigkeiten.

## Änderungsverfahren

1. Betroffene Fachposition bestimmen.
2. Kleinsten konsistenten Patch planen.
3. Eingaben, Ausgaben und Seiteneffekte vorab festlegen.
4. Fachmodul und Tests gemeinsam ändern.
5. Syntax und vollständige Testmatrix ausführen.
6. Dokumentation und Registry aktualisieren.
7. Branch- und Sicherheitsabgleich durchführen.
