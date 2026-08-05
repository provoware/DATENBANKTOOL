# TODO

Stand: Version `0.21.0-alpha.1`

## In dieser Iteration erledigt

1. [x] Nach exakter Restore-Sicherungsbestätigung optional nach einem neuen Protokollpfad fragen.
2. [x] Leere Eingabe ohne Änderung am bisherigen Restore-Befehl behandeln.
3. [x] Nur bei ausdrücklicher Eingabe `--restore-log PFAD` ergänzen.
4. [x] Absolute beziehungsweise mit `~` angegebene Pfade normalisieren und vollständig anzeigen.
5. [x] Vorhandene Ziele und Symlinks vor der Freigabe ablehnen.
6. [x] Keinen automatischen Zielvorschlag, keine Suche und keine Speicherung ergänzen.
7. [x] Geführte Aktion `Protokoll prüfen` unter „Sicherungen verwalten“ ergänzen.
8. [x] Geführte Prüfung ohne unnötige Datenbankabfrage ausführen.
9. [x] Genau einen vollständigen Protokollpfad sichtbar bestätigen lassen.
10. [x] Dieselbe sichere `verify-log`-Argumentliste wie im Terminal verwenden.
11. [x] Optionalen ausdrücklich eingegebenen SHA-256-Pin im Assistenten unterstützen.
12. [x] CLI-Option `--expected-protocol-sha256` ergänzen.
13. [x] Pinformat auf exakt 64 kleingeschriebene Hexzeichen begrenzen.
14. [x] Protokollidentität vor jeder JSON-Schemaauswertung prüfen.
15. [x] Falschen Pin fail-closed mit Code `2` ablehnen.
16. [x] Erfolgreiche Identitätsprüfung im Terminal und JSON ausgeben.
17. [x] Keine automatische Hashermittlung, Speicherung oder Historie einführen.
18. [x] Bestehende Protokoll- und Referenzdateien bytegenau unverändert lassen.
19. [x] Architektur über kleine Erweiterungsmodule statt Vergrößerung der Hauptklasse halten.
20. [x] 158 Tests unter Python 3.10 und 3.12 bestehen.
21. [x] Quick- und Standardabnahme mit jeweils 11/11 Prüfungen bestehen.

## Offener Hauptpunkt

1. [ ] Reale Laienabnahme auf einem Kubuntu-Zielsystem durch eine unerfahrene Testperson durchführen. Besonders beobachten: Verständnis der leeren optionalen Eingabe, Erkennung eines bereits vorhandenen Ziels, Auswahl von „Protokoll prüfen“, Interpretation der Ampelfarben und freiwillige SHA-Pin-Eingabe.

## Nicht blockierende Zielsystemprüfungen

- [ ] Geführten Restore einmal ohne und einmal mit neuem Protokollpfad durchführen.
- [ ] Vorhandenes Ziel und Symlink ausschließlich mit synthetischen Dateien ablehnen lassen.
- [ ] Geführte Prüfung mit Grün-, Gelb- und Rot-Befund beobachten.
- [ ] Richtigen und falschen SHA-Pin auf ext4 und einem USB-Ziel prüfen.

## Direkt folgender technischer Entwicklungsschritt

**Geführte Kubuntu-Abnahmesitzung:** Einen vollständig isolierten synthetischen Arbeitsbereich anlegen und die offenen Nutzerflüsse Schritt für Schritt mit fortsetzbarer Checkliste, Ampelbefunden und maschinenlesbarem Ergebnis durchführen. Keine echten Konfigurationen oder persönlichen Dateien verwenden.

## Alternative Verbesserung mit hohem Nutzen und geringem Risiko

**Optionaler Prüfberichtsexport:** Das Ergebnis von `verify-log` auf ausdrücklichen neuen Zielpfad als JSON oder Markdown veröffentlichen. Kein Überschreiben, keine automatische Benennung, Rotation oder Löschung.
