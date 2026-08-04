# Schwachstellen und aktuelle Grenzen

## Modulare CLI-Architektur

1. Die frühere zentrale `cli.py` ist beseitigt; die Fachmodule liegen jedoch nahe am festgelegten Höchstwert von 500 Zeilen. Besonders `cli_search.py` und `cli_index.py` müssen bei größeren Erweiterungen erneut geteilt werden.
2. Die Architekturtests prüfen Importgrenzen und gefährliche Aufrufe statisch. Sie ersetzen keine vollständige manuelle Sicherheitsprüfung neuer Fachlogik.
3. `CommandPolicy` beschreibt mögliche Seiteneffekte eines Befehls. Bei optionalen Schreibfunktionen wie FTS-Aufbau ist die Richtlinie bewusst konservativ und meldet grundsätzlich einen möglichen Indexschreibzugriff.
4. Die CLI-Fachmodule verwenden weiterhin `argparse.Namespace`. Streng typisierte Befehlsmodelle könnten später zusätzliche statische Sicherheit liefern.
5. Der alte Befehl `datenbanktool explain` und die neue Hilfe `datenbanktool help` bleiben aus Kompatibilitätsgründen parallel bestehen.

## Globale Wartungsregeln

6. Das Regelmanifest wird automatisch auf Struktur und Kernlimits geprüft, aber nicht jede textliche Regel kann vollständig maschinell erzwungen werden.
7. Dokumentationssynchronität benötigt weiterhin eine bewusste Iterationsprüfung.
8. Die Zeilengrenze verhindert neue Monolithen, sagt aber allein nichts über fachliche Komplexität einer Funktion aus.
9. Neue Laufzeitabhängigkeiten sind nicht technisch unmöglich, müssen aber laut Regelwerk ausdrücklich begründet und im Projektregister dokumentiert werden.

## Terminalbedienung und Hilfe

10. Die Oberfläche besitzt noch keine grafischen Dateiauswahlfenster.
11. Ordner- und Datenbankpfade werden als Text eingegeben oder eingefügt.
12. Alltagssuche arbeitet mit gepflegten Stichwörtern und nicht mit semantischer KI.
13. Fehlerhilfe nennt sichere Prüfstellen, führt aber absichtlich keine automatische Reparatur aus.
14. Hilfetexte sind derzeit deutschsprachig.

## Fachliche Grenzen

15. Die Ordnerübersicht besitzt JSON und HTML, aber noch keinen CSV-Export.
16. Ordnerwachstum zwischen zwei abgeschlossenen Scans wird noch nicht direkt zusammengefasst.
17. FTS5 durchsucht Metadaten und nicht automatisch den Inhalt aller Dateien.
18. Schreibende Originaldateioperationen bleiben gesperrt.
19. Vor einem stabilen Release fehlen Last- und Bedienabnahmen mit sehr großen realen Beständen.

## Sicherheitsfazit

Die Modularisierung reduziert Änderungsrisiko und verhindert neue unkontrollierte CLI-Monolithen. Keine bekannte Grenze rechtfertigt automatische Originaldateiänderungen. `CommandPolicy.validate()` weist solche Richtlinien weiterhin technisch ab.
