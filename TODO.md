# TODO

Stand: Version `0.18.0-alpha.1`

## In dieser Iteration erledigt

1. [x] Genau eine erkannte Konfigurationssicherung einer aktiven Vorlagendatei zuordnen.
2. [x] Such- und Zeitreihen-Sicherungen vollständig mit der aktiven Datei vergleichen.
3. [x] Hinzukommende, zu entfernende, zu ersetzende und unveränderte Vorlagen anzeigen.
4. [x] Vergleich im Terminal und als stabile JSON-Ausgabe bereitstellen.
5. [x] Den Vergleich vollständig lesend halten.
6. [x] Wiederherstellung auf grün geprüfte Katalogeinträge begrenzen.
7. [x] Indexsicherungen, unbekannte Pfade, beschädigte Dateien und Symlinks ablehnen.
8. [x] Exakte Wiederholung des Sicherungsdateinamens verlangen.
9. [x] `--yes` als zusätzliche ausdrückliche Bestätigung verlangen.
10. [x] Bereits identische Dateien ohne Überschreiben ablehnen.
11. [x] Vor jedem Überschreiben automatisch eine geprüfte Rückfallsicherung erzeugen.
12. [x] Aktive Datei und Sicherung unmittelbar vor der Mutation erneut per SHA-256 prüfen.
13. [x] Wiederherstellung atomar und mit Dateimodus `0600` veröffentlichen.
14. [x] Wiederhergestellte Datei bytegenau, per SHA-256 und über das vollständige Vorlagenschema nachprüfen.
15. [x] Bei fehlgeschlagener Nachprüfung automatisch aus der Rückfallsicherung zurücksetzen.
16. [x] Auch den automatischen Rückfall erneut nachprüfen.
17. [x] Ausgewählte Sicherung und Rückfallsicherung dauerhaft erhalten.
18. [x] Keine automatische Auswahl, Rotation, Alterslöschung oder Sammellöschung ergänzen.
19. [x] Geführte Startseite mit sichtbarem Nur-Lese-Vergleich und sicherer Argumentliste erweitern.
20. [x] CLI-Policies, Modulzuständigkeit, Größenlimits und Shellverbot prüfen.
21. [x] 139 Funktions-, Negativ-, Rückfall-, Dialog- und Architekturtests unter Python 3.10 und 3.12 bestehen.

## Offener Hauptpunkt

1. [ ] Reale Laienabnahme auf einem Kubuntu-Zielsystem durch eine unerfahrene Testperson durchführen. Besonders beobachten: Auswahl der richtigen Sicherung, Verständnis von Hinzufügen/Entfernen/Ersetzen, exakte Namenswiederholung, Rückfallsicherung und Unterschied zwischen Vergleich und tatsächlicher Wiederherstellung.

## Nicht blockierende Zielsystemprüfungen

- [ ] Wiederherstellung einer synthetischen Suchvorlagendatei auf ext4 durchführen.
- [ ] Wiederherstellung einer synthetischen Zeitreihen-Vorlagendatei auf einem USB-Ziel prüfen.
- [ ] Datenträger-voll-Fehler während der Veröffentlichung ausschließlich mit synthetischen Daten simulieren.
- [ ] Prozessabbruch vor und nach der atomaren Veröffentlichung kontrolliert dokumentieren.

## Direkt folgender technischer Entwicklungsschritt

**Wiederanlauf-Diagnosebefehl:** Eine rein lesende Terminal- und JSON-Übersicht ergänzen, die alle gespeicherten Wiederanlaufeinträge, Prüfstatus, Ordner, Index, Sitzung und Startbarkeit auch außerhalb der interaktiven Startseite zeigt. Der Befehl darf weder starten noch verwerfen.

## Alternative Verbesserung mit hohem Nutzen und geringem Risiko

**Wiederherstellungsprotokoll:** Nach einer erfolgreichen Konfigurations-Wiederherstellung optional ein kleines lokales JSON-Protokoll mit UTC-Zeit, aktiver Datei, ausgewählter Sicherung, Rückfallsicherung und den drei SHA-256-Werten erzeugen. Keine Inhalte, Geheimnisse, Rotation oder automatische Löschung.
