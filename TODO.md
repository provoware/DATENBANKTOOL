# TODO

Stand: Version `0.17.0-alpha.1`

## In dieser Iteration erledigt

1. [x] Wiederanlaufdatei auf Schema 2 mit begrenzter Eintragsliste migrieren.
2. [x] Bis zu zwölf verschiedene Indexdateien getrennt vormerken.
3. [x] Dieselbe Indexdatei deduplizieren und nur ihren neuesten Befehl behalten.
4. [x] Parallele Zugriffe mit lokaler Dateisperre koordinieren.
5. [x] Jeden Eintrag getrennt gegen Ordner, Indexdatei, Scanart, Stammordner und SQLite-Sitzung prüfen.
6. [x] Alle Wiederanläufe auf der Startseite mit Ordner, Index und Status anzeigen.
7. [x] Einen Eintrag gezielt fortsetzen, erhalten oder bewusst verwerfen.
8. [x] Nicht verfügbare Einträge sichtbar, aber nicht startbar halten.
9. [x] Bei Erfolg ausschließlich den zugehörigen Eintrag entfernen.
10. [x] Listenbegrenzung ohne Löschung von Index- oder Originaldateien prüfen.
11. [x] Optionale Konfigurationssicherung vor Ersetzen und Löschen von Suchvorlagen ergänzen.
12. [x] Dieselbe Sicherungsoption für Zeitreihen-Vorlagen ergänzen.
13. [x] Vor Sicherung JSON-Struktur, Schemaversion, Vorlagenliste und Symlinkfreiheit prüfen.
14. [x] Sicherung atomar mit Modus `0600` schreiben und danach per SHA-256 erneut prüfen.
15. [x] Fehlgeschlagene Sicherung vor der eigentlichen Vorlagenänderung stoppen.
16. [x] Keine automatische Rotation, Alterslöschung oder Sammellöschung einführen.
17. [x] Sicherungen in der bestehenden Sicherungsübersicht sichtbar machen.
18. [x] Doppelte CLI-Logik in einen gemeinsamen kleinen Helfer auslagern.
19. [x] Modulgrenze von höchstens 500 Zeilen wieder einhalten.
20. [x] 130 Funktions-, Negativ- und Architekturtests auf Python 3.10 und 3.12 bestehen.

## Offener Hauptpunkt

1. [ ] Reale Laienabnahme auf einem Kubuntu-Zielsystem durch eine unerfahrene Testperson durchführen. Besonders beobachten: Auswahl mehrerer Wiederanläufe, Unterschied zwischen „zurück“, „erhalten“ und „verwerfen“, optionale Sicherungsfrage und Auffinden der erzeugten Sicherung.

## Nicht blockierende Zielsystemprüfungen

- [ ] Zwei große synthetische Scans verschiedener Indexdateien kontrolliert unterbrechen und nach einem Neustart getrennt fortsetzen.
- [ ] Einen vorübergehend nicht eingehängten Quellordner anzeigen und nach erneutem Einhängen fortsetzen.
- [ ] Mehrere Konfigurationssicherungen auf ext4 und einem USB-Ziel prüfen.
- [ ] Fast vollen Datenträger ausschließlich mit synthetischen Testdaten simulieren.

## Direkt folgender technischer Entwicklungsschritt

**Wiederanlauf-Diagnosebefehl:** Eine rein lesende Terminal- und JSON-Übersicht ergänzen, die alle gespeicherten Einträge, ihren Prüfstatus, Ordner, Index, Sitzung und Startbarkeit auch außerhalb der interaktiven Startseite zeigt. Keine Ausführung und kein Verwerfen über den Diagnosebefehl.

## Alternative Verbesserung mit hohem Nutzen und geringem Risiko

**Geführtes Wiederherstellen einer Konfigurationssicherung:** Eine ausgewählte geprüfte JSON-Sicherung zunächst gegen aktive Datei, Schema, Inhalt und Prüfsumme vergleichen. Wiederherstellung nur einzeln, mit automatischer Rückfallsicherung und ausdrücklicher Bestätigung; keine automatische Auswahl oder Löschung.
