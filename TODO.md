# TODO

Stand: Version `0.19.0-alpha.1`

## In dieser Iteration erledigt

1. [x] Öffentlichen Befehl `index recovery` ergänzen.
2. [x] Alle gespeicherten Wiederanlaufeinträge getrennt und nur lesend validieren.
3. [x] Prüfstatus, Ordner, Indexdatei, Sitzung, Zustand, Phase und Startbarkeit im Terminal anzeigen.
4. [x] Vollständige JSON-Ausgabe ohne ANSI-Farbcodes bereitstellen.
5. [x] Gesamtzahl sowie startbare und nicht startbare Einträge ausgeben.
6. [x] Leere Wiederanlaufliste erfolgreich und eindeutig darstellen.
7. [x] Nachweisen, dass Diagnose weder `resume-run.json` noch die Indexdatei verändert.
8. [x] Keinen Start-, Verwerfen- oder Löschhandler im Diagnosebefehl anbieten.
9. [x] `--restore-log PFAD` als ausdrücklich optionale Restore-Option ergänzen.
10. [x] Protokoll erst nach erfolgreich bestätigter Wiederherstellung schreiben.
11. [x] UTC-Zeiten, drei Pfade und drei benannte SHA-256-Werte protokollieren.
12. [x] Konfigurationsinhalte, Vorlagen, Argumente und Geheimnisse vollständig ausschließen.
13. [x] Protokoll atomar und mit Dateimodus `0600` veröffentlichen.
14. [x] Existierende Ziele ohne Überschreiben ablehnen.
15. [x] Ohne Option keinerlei Protokoll erzeugen.
16. [x] Keine automatische Benennung, Auswahl, Rotation oder Löschung ergänzen.
17. [x] Teilfehler sauber behandeln: Restore bleibt erfolgreich, Protokollfehler liefert Code `1`.
18. [x] CLI-Policy, Parser, Modulzuständigkeit, Größenlimits und Shellverbot erweitern.
19. [x] 145 Funktions-, Negativ-, Inhaltsschutz- und Architekturtests unter Python 3.10 und 3.12 bestehen.
20. [x] Quick- und Standardabnahme mit jeweils 11/11 Prüfungen bestehen.

## Offener Hauptpunkt

1. [ ] Reale Laienabnahme auf einem Kubuntu-Zielsystem durch eine unerfahrene Testperson durchführen. Besonders beobachten: Verständnis der rein lesenden Diagnose, Unterscheidung zwischen startbar und nicht startbar, bewusste Angabe eines neuen Protokollpfads sowie Meldung bei bereits vorhandenem Ziel.

## Nicht blockierende Zielsystemprüfungen

- [ ] Zwei reale unterbrochene synthetische Scans gemeinsam über `index recovery` prüfen.
- [ ] Einen vorübergehend ausgehängten Quellordner als nicht startbar anzeigen.
- [ ] Restore-Protokoll auf ext4 und einem USB-Ziel mit Modus `0600` kontrollieren.
- [ ] Vorhandenes Protokollziel und vollen Datenträger ausschließlich mit synthetischen Daten testen.

## Direkt folgender technischer Entwicklungsschritt

**Wiederherstellungsprotokoll-Prüfbefehl:** Eine ausdrücklich ausgewählte Protokolldatei vollständig lesend auf Schema, UTC-Zeiten, drei Pfade und drei SHA-256-Werte prüfen und vorhandene Dateien gegen die protokollierten Werte vergleichen. Keine Wiederherstellung, Änderung oder Löschung.

## Alternative Verbesserung mit hohem Nutzen und geringem Risiko

**Geführte Protokollauswahl:** Die bestehende Startseite nach der exakten Restore-Bestätigung optional nach einem neuen Protokollpfad fragen und ausschließlich dann `--restore-log` an die sichere Argumentliste anhängen. Kein automatisch vorgeschlagener oder überschreibbarer Zielpfad.
