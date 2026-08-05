# TODO

Stand: Version `0.20.0-alpha.1`

## In dieser Iteration erledigt

1. [x] Öffentlichen Befehl `index backups verify-log PROTOKOLL` ergänzen.
2. [x] Protokolldatei ausschließlich über einen ausdrücklich angegebenen Pfad auswählen.
3. [x] Symlink-Protokolle ohne Folgen ablehnen.
4. [x] UTF-8-JSON und exakt das feste Schema `1` validieren.
5. [x] Ereignis `configuration_restore` und Konfigurationsart prüfen.
6. [x] Beide ISO-8601-Zeitfelder ausdrücklich auf UTC prüfen.
7. [x] Zeitreihenfolge zwischen Restore-Abschluss und Protokollerzeugung prüfen.
8. [x] Genau drei unterschiedliche absolute Dateipfade verlangen.
9. [x] Genau drei benannte SHA-256-Werte mit jeweils 64 Kleinbuchstaben-Hexzeichen verlangen.
10. [x] Fehlende und unerwartete Schemafelder ablehnen.
11. [x] Drei referenzierte Dateien mit `O_NOFOLLOW` ausschließlich lesend öffnen.
12. [x] Dateiinhalte gestreamt hashen statt vollständig in den Speicher zu laden.
13. [x] Übereinstimmung, fehlende Datei, Hashabweichung, Symlink und Lesefehler getrennt anzeigen.
14. [x] Stabile Terminal- und JSON-Ausgaben bereitstellen.
15. [x] Rückgabecodes `0`, `1` und `2` eindeutig trennen.
16. [x] Nachweisen, dass Protokoll und alle referenzierten Dateien unverändert bleiben.
17. [x] Keinen Restore-, Änderungs- oder Löschhandler anbieten.
18. [x] Eigenes CLI-Fachmodul mit rein lesender `CommandPolicy` verwenden.
19. [x] Parser, Modulzuständigkeit, Größenlimits und Shellverbot automatisiert prüfen.
20. [x] 151 Funktions-, Negativ-, Schema-, Integritäts- und Architekturtests unter Python 3.10 und 3.12 bestehen.
21. [x] Quick- und Standardabnahme mit jeweils 11/11 Prüfungen bestehen.

## Offener Hauptpunkt

1. [ ] Reale Laienabnahme auf einem Kubuntu-Zielsystem durch eine unerfahrene Testperson durchführen. Besonders beobachten: Verständnis von Grün/Gelb/Rot, Unterschied zwischen ungültigem Protokoll und fehlender Datei, Bedeutung einer Hashabweichung sowie Sicherheit, dass keine Wiederherstellung ausgeführt wird.

## Nicht blockierende Zielsystemprüfungen

- [ ] Gültiges Restore-Protokoll auf ext4 mit drei vorhandenen Dateien prüfen.
- [ ] Eine vorübergehend ausgehängte Sicherung als fehlend und nicht als beschädigt darstellen.
- [ ] Eine bewusst kopierte und danach veränderte Datei als Hashabweichung erkennen.
- [ ] Protokoll- und Referenz-Symlinks auf einem Kubuntu-Zielsystem ablehnen.
- [ ] Sehr große synthetische Referenzdatei mit begrenztem Arbeitsspeicher gestreamt prüfen.

## Direkt folgender technischer Entwicklungsschritt

**Geführte Protokollprüfung:** Die Startseite unter „Sicherungen verwalten“ um eine rein lesende Aktion erweitern. Der Nutzer gibt exakt eine Protokolldatei an, sieht vorab den vollständigen Pfad und erhält dieselbe Grün/Gelb/Rot-Auswertung wie im Terminal. Kein automatisches Suchen, Starten, Ändern oder Löschen.

## Alternative Verbesserung mit hohem Nutzen und geringem Risiko

**Optionaler Protokoll-SHA-Pin:** `verify-log` optional einen erwarteten SHA-256-Wert der Protokolldatei entgegennehmen lassen. Vor der Schemaauswertung wird die Identität der ausdrücklich ausgewählten Datei geprüft. Keine Nebenwirkung, keine automatische Ermittlung und keine gespeicherte Historie.
