# Analyse-Punkte

## Ergebnis dieser Iteration

Die Startseite erklärt Funktionen nicht mehr nur mit einem einzelnen Textblock. Nutzer können zwischen kurzer Orientierung, ausführlicher Wirkungserklärung, vollständiger Schrittanleitung und Hilfe zur konkreten Eingabe wechseln. Nach Fehlern zeigt das Tool einen sicheren nächsten Prüfweg.

## Vollständig gelöste Punkte

1. Jede Hauptfunktion besitzt eine kurze Soforthilfe.
2. `?NUMMER` zeigt ausführliche Detailhilfe, ohne die Funktion zu starten.
3. `gNUMMER` zeigt eine vollständige Schrittfolge.
4. `?` erklärt das aktuelle Eingabefeld und wiederholt danach dieselbe Frage.
5. Hilfen nennen Schreibwirkung und Risiko ausdrücklich.
6. Hilfen erklären Voraussetzungen vor dem Start.
7. Hilfen erklären, woran ein erfolgreicher Abschluss erkennbar ist.
8. Typische Probleme erhalten eine konkrete sichere Lösung.
9. Fehlercodes führen zu kontextbezogener Fehlerhilfe.
10. Die Fehlerhilfe führt keine automatische Reparatur aus.
11. `datenbanktool help` funktioniert unabhängig von der interaktiven Startseite.
12. Drei Hilfestufen stehen bereit: `quick`, `detail` und `guided`.
13. Themen können über Alltagsbegriffe gesucht werden.
14. Hilfedaten können als JSON ausgegeben werden.
15. Unbekannte Themen enden kontrolliert mit Rückgabecode 2.
16. Hilfekatalog und Startseitenlogik sind voneinander getrennt.
17. Der alte Importpfad bleibt kompatibel, enthält aber keine zweite aktive Logik.
18. Die große `cli.py` wurde nicht weiter vergrößert.
19. Originaldateien bleiben durch sämtliche Hilfefunktionen unverändert.
20. 48 Tests laufen unter Python 3.10 und 3.12 erfolgreich.

## Zentrale Architekturentscheidungen

### Hilfe auf Wunsch statt Zwangsdialoge

Zusätzliche Pflichtfragen würden erfahrene Nutzer ausbremsen und bestehende Abläufe verändern. Deshalb bleibt die normale Nummernauswahl direkt nutzbar; tiefergehende Hilfe wird gezielt über `?NUMMER`, `gNUMMER` oder `?` aufgerufen.

### Ein zentraler Hilfekatalog

Titel, Kurzbeschreibung, Schreibwirkung, Voraussetzungen, Schritte, Erfolgskontrolle und typische Probleme liegen in einem zentralen Modul. Dadurch können Startseite, Hilfebefehl und spätere GUI dieselben Inhalte verwenden.

### Keine automatische Fehlerreparatur

Ein Fehlercode kann viele Ursachen besitzen. Automatisches Korrigieren könnte falsche Pfade, Datenbanken oder Berechtigungen verändern. Die Hilfe nennt deshalb sichere Prüfstellen und überlässt die Entscheidung dem Nutzer.

### Alltagssuche ohne Online-Abhängigkeit

Die Hilfesuche arbeitet vollständig offline über Funktionsnamen, Beschreibungen und gepflegte Stichwörter. Sie bleibt schnell, nachvollziehbar und ohne Cloud-Abhängigkeit.

### Kompatibilität ohne doppelte Logik

`core/terminal_home.py` bleibt als kleiner Importadapter bestehen. Die tatsächliche Implementierung liegt nur noch in `core/guided_home.py`.

## Erkannte nächste Analysepunkte

1. Große `cli.py` in getrennte Parser- und Ausführungsmodule zerlegen.
2. Hilfetexte künftig direkt aus den Fachmodulen registrieren, ohne Importzyklen zu erzeugen.
3. CSV-Export der Ordnerübersicht ergänzen.
4. Ordnerwachstum zwischen Scan-Sitzungen darstellen.
5. Hilfekatalog später für Übersetzungen vorbereiten.
6. Bedienabnahme mit Linux-Laien durchführen.
7. Hilfesuche mit weiteren realen Nutzerformulierungen testen.
8. Sehr große Bestände unter festen Ressourcenlimits prüfen.

## Fazit

Die Bedienung ist deutlich fehlertoleranter und verständlicher, ohne den Sicherheitsvertrag aufzuweichen. Hilfe ist jederzeit erreichbar, bleibt vollständig offline und löst keine versteckten Datenänderungen aus.
