# TODO

## P0 – Sicherheits- und Datenkern

1. [x] Projektstruktur, Versionierung und rein lesenden Scanner anlegen.
2. [x] Dateikategorien, Dateinamenprüfung und exakte Duplikaterkennung anlegen.
3. [x] Atomaren JSON-Bericht und Basistests anlegen.
4. [ ] SQLite-Index mit Schema-Version, Migration und Reparaturmodus entwickeln.
5. [ ] Scan-Journal für Pause, Fortsetzen und Wiederaufnahme nach Absturz entwickeln.
6. [ ] Dateiidentität aus Gerät, Inode, Größe, Zeitwerten und optionalem Hash robust modellieren.
7. [ ] Vorschauplan als unveränderliches Manifest entwickeln.
8. [ ] Konfliktprüfung für Zielpfade, Rechte, Speicherplatz und Dateisystemgrenzen entwickeln.
9. [ ] Transaktionale Kopier-, Verschiebe- und Umbenennungsengine mit Undo entwickeln.
10. [ ] Quarantäne und Papierkorb statt Direktlöschung entwickeln.

## P1 – Laienoberfläche

11. [ ] PySide6-Oberfläche mit Einfach-, Geführt- und Expertenmodus entwickeln.
12. [ ] Ordnerauswahl, Scanfortschritt, Pause, Abbruch und verständliche Fehleranzeige entwickeln.
13. [ ] Ergebnis-Dashboard mit Ampel, Fundgruppen und empfohlenen Aktionen entwickeln.
14. [ ] Bild-, Audio-, Video-, Text-, PDF-, Archiv- und Codevorschau entwickeln.
15. [ ] Große Schaltflächen, Touchbedienung, Tastaturführung und hohe Kontraste prüfen.
16. [ ] Jede technische Meldung mit Ursache, Wirkung und sicherer Handlung ergänzen.

## P1 – Suche und Ordnung

17. [ ] Schnellsuche über Name, Pfad, Typ, Größe, Datum und Metadaten entwickeln.
18. [ ] Gespeicherte Filter, Suchprofile und transparente Regelkombinationen entwickeln.
19. [ ] Sortierpläne nach Medientyp, Datum, Projekt, Künstler und frei definierbaren Regeln entwickeln.
20. [ ] Stapelumbenennung mit Vorschau, Nummerierung und Kollisionsschutz entwickeln.
21. [ ] Leere, extrem große, tief verschachtelte und unzugängliche Ordner erkennen.
22. [ ] Archive inventarisieren und optional ohne Entpacken prüfen.
23. [ ] Codeprojekte erkennen, Buildreste markieren und Projektgrenzen darstellen.

## P2 – Medienintelligenz

24. [ ] FFmpeg/ffprobe- und MediaInfo-Prüfung integrieren.
25. [ ] Audio-Fingerprints für inhaltlich gleiche Audiodateien entwickeln.
26. [ ] Perceptual Hashes für ähnliche Bilder und Videos entwickeln.
27. [ ] Textähnlichkeit und Normalisierungsvarianten entwickeln.
28. [ ] Beschädigte, unvollständige oder falsch benannte Medien erkennen.

## P2 – Betrieb und Release

29. [ ] CPU-, RAM-, Datenträger- und I/O-Limits entwickeln.
30. [ ] AppImage oder portable Linux-Ausgabe mit Doppelklick-Start entwickeln.
31. [ ] Ruff, MyPy, Bandit, pip-audit und Coverage als Qualitätsgates einrichten.
32. [ ] Reale Tests auf Kubuntu, externen HDDs, NTFS, exFAT und schreibgeschützten Medien durchführen.

## Erledigte Punkte

- Grundarchitektur getrennt in CLI, Modelle, Klassifizierung, Benennungsprüfung und Scanner.
- Rein lesender Standardmodus.
- Symbolischen Links wird standardmäßig nicht gefolgt.
- Vorhandene Berichte werden nicht still überschrieben.
- Exakte Duplikate werden optional per SHA-256 geprüft.
- Basisprüfungen lokal erfolgreich ausgeführt.

## Erinnerungsliste für spätere Maßnahmen

1. Keine schreibende Funktion vor fertigem Vorschau-, Journal- und Undo-Vertrag freigeben.
2. Große Sammlungen niemals vollständig im Arbeitsspeicher halten.
3. Originaldateien bei Duplikaten nie automatisch bestimmen.
4. Wechselmedien und getrennte Dateisysteme als Normalfall behandeln.
5. Laienmodus darf Fachbegriffe anzeigen, muss sie aber direkt erklären.
