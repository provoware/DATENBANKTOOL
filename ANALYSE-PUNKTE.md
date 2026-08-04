# Analyse-Punkte

## Ergebnis dieser Iteration

Das Tool zeigt nicht mehr nur einzelne Dateien, sondern erklärt jetzt auch die Struktur ganzer Ordner. Speicherbedarf, Dateimengen, Namenshinweise, Duplikate und größte Einzeldateien werden verständlich zusammengeführt.

## Vollständig gelöste Punkte

1. Ordnerwerte werden aus einem abgeschlossenen Snapshot rein lesend berechnet.
2. Direkte Dateien und Dateien in Unterordnern werden getrennt ausgewiesen.
3. Gesamtgrößen werden ohne Laden des gesamten Dateiinhalts ermittelt.
4. Größte Platzfresser werden stabil nach Größe und Pfad sortiert.
5. Große Ergebnislisten besitzen Filter, Seiten und feste Sortierungen.
6. Ampeln enthalten Farbe, Farbnamen, Statuswort und Begründung.
7. Farben können automatisch, dauerhaft oder gar nicht verwendet werden.
8. `NO_COLOR` wird als etablierter Ausschalter respektiert.
9. JSON-Ausgaben bleiben maschinenlesbar und frei von Farbcodes.
10. HTML-Berichte besitzen echte Hover-Texte und ARIA-Beschriftungen.
11. Terminalausgaben besitzen kontextbezogene Hinweise statt unzuverlässiger Maus-Tooltips.
12. Funktionsbeschreibungen erklären Zweck, Wirkung, Schreibzugriffe, Risiko und Beispiel.
13. Suchfilter können als verständlich benannte Vorlagen gespeichert werden.
14. Vorlagen werden außerhalb des SQLite-Indexes gespeichert.
15. Vorlagen werden atomar geschrieben und standardmäßig nur für den Benutzer freigegeben.
16. Überschreiben und Löschen benötigen ausdrückliche Freigaben.
17. Gespeicherte Filter können beim Start gezielt überschrieben werden.
18. Originaldateien bleiben in allen neuen Funktionen unverändert.

## Fachliche Entscheidungen

### Ampel statt versteckter Punktzahl

Eine undurchsichtige Bewertungspunktzahl wäre für Laien schwer nachvollziehbar. Deshalb zeigt jede Ampel direkt die erkannten Gründe. Die Ampel priorisiert nur die Reihenfolge der Prüfung.

### Farben niemals allein

Farben können wegen Sehschwächen, Terminaleinstellungen oder Ausdrucken fehlen. Darum bleiben Klartext und Begründung immer erhalten.

### Ordnerwerte aus dem Snapshot

Die Übersicht greift auf denselben geprüften Snapshot wie Suche und Berichte zurück. Dadurch entstehen keine widersprüchlichen Ergebnisse durch einen parallel veränderten Dateibestand.

### Vorlagen außerhalb der Datenbank

Suchvorlagen sind persönliche Bedienkonfiguration. Sie werden getrennt vom gemeinsam nutzbaren Dateiindex gespeichert und können keinen Index beschädigen.

### Tooltips passend zur Oberfläche

HTML unterstützt verlässliche Hover-Tooltips. Ein Terminal unterstützt dies nicht einheitlich. Dort sind sichtbare Hinweise und der Befehl `explain` die robustere, barriereärmere Lösung.

## Erkannte nächste Analysepunkte

1. Ampelschwellen später als verständliche Profile konfigurierbar machen.
2. Ordnerwachstum zwischen zwei Scan-Sitzungen anzeigen.
3. CSV-Export für Ordnerübersichten ergänzen.
4. Gleichzeitige Vorlagenänderungen mit einem kleinen Konfigurationslock absichern.
5. Vorlagenexport und -import mit Versionsprüfung entwickeln.
6. Ein nummeriertes Startmenü als Übergang zur grafischen Oberfläche bauen.
7. Bedienabnahme mit vollständigen Linux-Laien durchführen.
8. Ampeldarstellung in dunklen und hellen Terminalthemen prüfen.
9. Sehr große Ordnerbestände mit Millionen Dateien messen.
10. Spätere GUI-Tooltips aus denselben zentralen Hilfetexten speisen.

## Architektur-Fazit

Die Bedienlogik ist jetzt deutlich verständlicher, ohne den Sicherheitsvertrag aufzuweichen. Farben, Ampeln und Vorlagen liegen über dem rein lesenden Datenkern. Automatische Originaldateiänderungen bleiben weiterhin korrekt blockiert.
