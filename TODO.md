# TODO

## Erledigt

1. [x] Rein lesenden Scanner anlegen.
2. [x] Dateiklassifizierung implementieren.
3. [x] Dateinamenrisiken erkennen.
4. [x] Große Dateien markieren.
5. [x] Exakte Duplikate per SHA-256 erkennen.
6. [x] JSON-Berichte atomar schreiben.
7. [x] Projekt- und Sicherheitsregister einführen.
8. [x] SQLite-Index mit Schema-Versionierung implementieren.
9. [x] V1→V2-Migration implementieren.
10. [x] Batch-Import transaktional umsetzen.
11. [x] Scan-Wiederaufnahme mit Checkpoint umsetzen.
12. [x] Hashing-Wiederaufnahme vorbereiten.
13. [x] Reparaturmodus mit Sicherheitskopie implementieren.
14. [x] CSV-Berichte mit Filtern implementieren.
15. [x] HTML-Berichte mit Filtern implementieren.

## Priorität P0 – nächster technischer Block

1. [ ] Inkrementellen Re-Scan abgeschlossener Sitzungen entwickeln.
2. [ ] Änderungen, neue und entfernte Dateien sicher abgleichen.
3. [ ] Dateisystemidentität und Mountwechsel erfassen.
4. [ ] Fortschrittsereignisse für Scan und Hashing einführen.
5. [ ] Kontrolliertes Pausieren und Abbrechen ohne Testgrenze umsetzen.
6. [ ] Wiederaufnahme bei entferntem Checkpoint sicher lösen.
7. [ ] Simultane Schreibzugriffe über Anwendungslock verhindern.
8. [ ] Datenbank-Backup und Wiederherstellung als eigenes CLI-Kommando ergänzen.

## Priorität P1 – Suche und Bedienung

9. [ ] Indexsuche nach Pfad, Dateiname, Endung, Kategorie und Größe ergänzen.
10. [ ] FTS5 für freigegebene Textinhalte evaluieren.
11. [ ] gespeicherte Filterprofile einführen.
12. [ ] Ergebnisstatistik nach Kategorie, Größe und Warnung ergänzen.
13. [ ] HTML-Ausgabe für Millionen Zeilen paginieren oder aufteilen.
14. [ ] PySide6-Grundoberfläche mit Einfach-/Geführt-/Expertenmodus anlegen.
15. [ ] Fortschritt, Pause, Abbruch und Wiederaufnahme laiengerecht darstellen.

## Priorität P2 – Medien und Prüfung

16. [ ] ffprobe/MediaInfo-Abstraktion entwickeln.
17. [ ] Bild-, Audio-, Video- und Textvorschau einführen.
18. [ ] beschädigte und falsch benannte Medien erkennen.
19. [ ] Audio-Fingerprints und Bildähnlichkeit getrennt von exakten Duplikaten umsetzen.
20. [ ] Archive ohne unkontrolliertes Entpacken inventarisieren.

## Weiterhin gesperrt

21. [ ] Stapelumbenennung.
22. [ ] Verschieben und Sortieren.
23. [ ] Quarantäne und Papierkorb.
24. [ ] Undo-Journal.
25. [ ] Recovery nach Abbruch schreibender Operationen.
26. [ ] Freigabe schreibender Dateioperationen erst nach vollständigen Sicherheitsgates.
