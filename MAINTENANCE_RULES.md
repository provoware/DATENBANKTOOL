# Globale Wartungs- und Entwicklungsregeln

Diese Regeln gelten projektweit. Die maschinenlesbare Fassung steht in
`maintenance_rules.json`; Architektur- und Sicherheitstests erzwingen die wichtigsten
Grenzen automatisch.

## 1. Öffentliche Bedienung bleibt stabil

Bestehende Befehlsnamen, Parameter, Rückgabecodes und Maschinenfelder werden nicht
unbemerkt verändert. Notwendige Änderungen erhalten Version, Changelog und
Kompatibilitätstest.

## 2. Ein Fachbereich pro Modul

Parser und Ausführung einer Funktion liegen im selben Fachmodul:

- `cli_scan.py`: einmalige Scans,
- `cli_search.py`: Suche und Suchvorlagen,
- `cli_reports.py`: Ordner-, Änderungs- und Dateiberichte,
- `cli_folder_compare.py`: Ordnervergleich,
- `cli_acceptance.py`: reproduzierbare Abnahmetests,
- `cli_index.py`: Indexverwaltung,
- `cli_help.py`: klassische Funktionsbeschreibung,
- `cli.py`: nur Zusammensetzung, Dispatch und zentrale Fehlergrenze.

`cli.py` darf keine Fachlogik zurückerhalten.

## 3. Abhängigkeiten zeigen nur nach innen

CLI-Fachmodule dürfen gemeinsame CLI-Hilfen und Core-Module importieren. Sie
importieren niemals `cli.py` und erzeugen keine zyklischen Abhängigkeiten.

## 4. Jede Wirkung wird deklariert

Jeder Parser wird über `bind_handler()` mit einer `CommandPolicy` verbunden. Darin
steht, ob Originaldateien gelesen, Indexdaten, Berichte, Sicherungen,
Konfigurationen oder ausschließlich synthetische Testdaten geschrieben werden.

## 5. Originaldateien bleiben geschützt

Schreibzugriffe auf gescannte Originaldateien sind global gesperrt, bis ein eigener,
versionierter Sicherheitsvertrag mit Vorschau, Journal, Rückgängig-Funktion,
Quarantäne und vollständigen Tests beschlossen wurde.

## 6. Testdaten bleiben strikt isoliert

Last- und Abnahmetests dürfen Daten ausschließlich in einem ausdrücklich gewählten,
noch nicht vorhandenen Arbeitsordner erzeugen.

- Vorhandene Arbeitsordner werden abgelehnt.
- Persönliche Dateien werden nicht als Testdaten verwendet.
- Ein Vorher-/Nachher-Manifest prüft Pfad, Größe und Änderungszeit jeder Quelldatei.
- Testberichte nennen klar, dass eine automatisierte Prüfung keine reale Testperson
  ersetzt.

## 7. Schreibvorgänge sind atomar und ausdrücklich

Ersetzbare Dateien werden zuerst temporär geschrieben und erst nach erfolgreicher
Prüfung atomar freigegeben. Vorhandene Ziele werden ohne ausdrückliche Option nicht
überschrieben.

## 8. Vollständige Exporte sind ausdrücklich

Terminalseiten bleiben begrenzt. Ein vollständiger Export über alle Filtertreffer
benötigt einen sichtbaren Schalter wie `--all-pages`. Die Ausgabe nennt den tatsächlichen
Exportumfang.

## 9. Keine Shell-Auswertung

CLI-Fachmodule verwenden weder `shell=True`, `os.system`, `eval` noch `exec`.
Nutzereingaben bleiben strukturierte Argumente.

## 10. Rückgabecodes sind einheitlich

- `0`: erfolgreich,
- `1`: fachlich abgeschlossen, aber mindestens ein Abnahmekriterium verfehlt,
- `2`: kontrollierter Eingabe-, Datei-, SQLite- oder Sicherheitsfehler.

Handler liefern immer `int`.

## 11. Menschen- und Maschinenformate bleiben getrennt

JSON, CSV und andere Maschinenformate enthalten keine ANSI-Farben, Tooltips oder
Bedienhinweise. Farben ergänzen ausschließlich sichtbaren Klartext.

## 12. Größenlimits verhindern neue Monolithen

- `cli.py`: höchstens 150 Zeilen,
- jedes `cli_*.py`-Fachmodul: höchstens 500 Zeilen.

Wird ein Limit erreicht, wird vor der nächsten Funktion weiter aufgeteilt.

## 13. Jede Änderung erhält vollständige Prüfungen

Neue oder verschobene Funktionen benötigen Syntax-, Parser-, Handler-, Fehler-,
Sicherheits- und Rückwärtskompatibilitätstests. GitHub Actions prüft Python 3.10 und
3.12 mit Warnungen als Fehler.

Der aktuelle Abnahmevertrag umfasst zusätzlich:

- Quick-Profil mit 600 Dateien,
- Standard-Profil mit 10.000 Dateien,
- vollständigen Ordner-CSV-Export,
- Laufzeit- und Python-Speichergrenzen,
- Quelldaten-Manifest,
- archivierte JSON-, Markdown-, CSV- und Laien-Checklistenberichte.

## 14. Dokumentation und Registry bleiben synchron

README, Changelog, TODO, Upgrade-Pool, Schwachstellenanalyse, Analyse-Punkte,
Entwicklerdokumentation, Projektregister und diese Regeln werden am Ende jeder
Iteration gemeinsam geprüft.

## 15. Abhängigkeiten bleiben minimal

Neue Laufzeitabhängigkeiten benötigen eine dokumentierte Begründung, ihre
Offline-Auswirkung und eine geprüfte Alternative. Der Zielwert bleibt null externe
Laufzeitabhängigkeiten.

## Änderungsverfahren

1. Betroffene Fachposition bestimmen.
2. Kleinsten konsistenten Patch planen.
3. Eingaben, Ausgaben und Seiteneffekte vorab festlegen.
4. Fachmodul und Tests gemeinsam ändern.
5. Syntax, Testmatrix und Abnahmeprofile ausführen.
6. Dokumentation und Registry aktualisieren.
7. Branch-, Artefakt- und Sicherheitsabgleich durchführen.
