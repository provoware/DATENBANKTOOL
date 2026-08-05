# TODO

Stand: Version `0.16.0-alpha.1`

## In dieser Iteration erledigt

1. [x] Bestätigten Vollscan- oder Re-Scan-Befehl als eigenen Wiederanlaufdatensatz speichern.
2. [x] Wiederanlauf nur nach Prüfung von Ordner, Indexdatei, Scanart und SQLite-Sitzung anbieten.
3. [x] Ordner, Index, Scan-Nummer, Phase, Dateizahl und vollständigen `--resume`-Befehl anzeigen.
4. [x] Fortsetzung erst nach sichtbarer Bestätigung starten.
5. [x] Ablehnung und Abbruch ohne Verlust des Wiederanlaufhinweises behandeln.
6. [x] Veraltete Hinweise ohne fortsetzbare SQLite-Sitzung bereinigen.
7. [x] Index- und Konfigurationssicherungen nach Typ, Alter, Größe und Zustand auflisten.
8. [x] SQLite-Sicherungen nur lesend mit `quick_check` prüfen.
9. [x] Konfigurationssicherungen auf JSON-Struktur und Schemaversion prüfen.
10. [x] Genau eine katalogisierte Sicherung nach Pfad-, Namens- und Ja-Bestätigung löschen.
11. [x] Aktive Dateien, unbekannte Pfade und Symlinks vom Löschen ausschließen.
12. [x] Zentrale dauerhafte Schreib- und Löschhelfer gegen Symlink-Ziele härten.
13. [x] Startseitenpunkt 7 zu „Sicherungen verwalten“ ausbauen.
14. [x] CLI-, Startseiten-, Architektur-, Negativ- und Wiederanlauftests ergänzen.
15. [x] Version und Pflichtdokumentation auf `0.16.0-alpha.1` synchronisieren.

## Offener Hauptpunkt

1. [ ] Reale Laienabnahme auf einem Kubuntu-Zielsystem durch eine unerfahrene Testperson durchführen. Besonders beobachten: Wiederanlaufhinweis, sichtbarer Befehl, Nein/Ja-Entscheidung, Sicherungsstatus und Einzellöschung.

## Nicht blockierende Zielsystemprüfungen

- [ ] Rechner während eines großen synthetischen Scans kontrolliert neu starten und den Wiederanlauf über `datenbanktool start` dokumentieren.
- [ ] Sicherungsübersicht mit realem ext4- und USB-Ziel prüfen.
- [ ] Fast vollen Datenträger ausschließlich mit synthetischen Testdaten simulieren.
- [ ] Fehlende oder vorübergehend nicht eingehängte Quellordner beim Wiederanlauf prüfen.

## Direkt folgender technischer Entwicklungsschritt

**Mehrere unabhängige Wiederanläufe:** Statt eines einzelnen Hinweises eine begrenzte Liste unterbrochener Scans für verschiedene Indexdateien führen. Jeden Eintrag separat validieren, anzeigen, starten oder bewusst verwerfen.

## Alternative Verbesserung mit hohem Nutzen und geringem Risiko

**Konfigurations-Sicherungen vor Änderungen:** Vor dem Ersetzen oder Löschen von Such- und Zeitreihen-Vorlagen optional eine geprüfte, zeitgestempelte JSON-Sicherung erstellen. Keine automatische Löschung oder Rotation.
