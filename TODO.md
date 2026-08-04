# TODO

## In dieser Iteration erledigt

1. [x] Soforthilfe direkt in der Startseite ergänzen.
2. [x] Detailhilfe über `?NUMMER` ergänzen.
3. [x] Geführte Schrittanleitung über `gNUMMER` ergänzen.
4. [x] Hilfe für einzelne Eingabefelder über `?` ergänzen.
5. [x] Kontextbezogene Fehlerhilfe nach Fehlercodes anzeigen.
6. [x] Eigenständigen Befehl `datenbanktool help` entwickeln.
7. [x] Hilfestufen `quick`, `detail` und `guided` anbieten.
8. [x] Hilfethemen über Alltagswörter mit `--find` suchen.
9. [x] Hilfen maschinenlesbar als JSON ausgeben.
10. [x] Hilfekatalog zentral und unveränderlich definieren.
11. [x] Startseitenlogik in ein eigenes Modul auslagern.
12. [x] Alten Importpfad als schmale Kompatibilitätsschicht erhalten.
13. [x] Fehlerfälle ohne automatische Reparatur sicher erklären.
14. [x] 48 automatisierte Tests unter Python 3.10 und 3.12 erfolgreich ausführen.

## Noch offen

1. [ ] Große `cli.py` in kleinere Befehlsmodule aufteilen.
2. [ ] Ordnerübersicht zusätzlich als CSV exportieren.
3. [ ] Ordnerwachstum zwischen zwei Scan-Sitzungen vergleichen.
4. [ ] Abnahme mit sehr großen realistischen Beständen und Linux-Laien durchführen.

## Direkt folgender einfacher Schritt

Den großen Befehlsblock in kleinere, klar benannte Module teilen. Suche, Berichte, Verwaltung und Scan erhalten getrennte Dateien, ohne die sichtbaren Befehle zu ändern.

## Sichere Zusatzverbesserung

Die Ordnerübersicht als CSV speichern, damit sie direkt in LibreOffice Calc geöffnet werden kann.
