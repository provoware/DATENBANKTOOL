# TODO

## Erledigt

1. [x] Rein lesenden Verzeichnisscanner entwickeln.
2. [x] Medien-, Text-, Archiv-, Code- und Dokumentklassifizierung entwickeln.
3. [x] Problematische Dateinamen prüfen.
4. [x] Exakte Duplikate per SHA-256 erkennen.
5. [x] SQLite-Index mit Schema-Versionierung entwickeln.
6. [x] Batch-Import transaktional absichern.
7. [x] Unterbrochene Vollindizierung fortsetzen.
8. [x] Reparaturmodus mit Sicherung entwickeln.
9. [x] CSV- und HTML-Berichte mit Filtern entwickeln.
10. [x] Inkrementellen Re-Scan entwickeln.
11. [x] Neue Dateien erkennen.
12. [x] Geänderte Dateien erkennen.
13. [x] Verschobene Dateien sicher erkennen.
14. [x] Entfernte Dateien erkennen.
15. [x] Unveränderte Hashwerte wiederverwenden.
16. [x] Prozesslock für schreibende Indexaktionen entwickeln.
17. [x] Persistente Fortschrittsereignisse entwickeln.
18. [x] Sitzungsübersicht entwickeln.
19. [x] Konsistente Indexsicherung entwickeln.
20. [x] Geprüfte Wiederherstellung mit Sicherheitskopie entwickeln.
21. [x] Python-3.10-/3.12-CI einrichten.
22. [x] Schema-2→3-Migration testen.
23. [x] Inode-Wiederverwendung als Fehlklassifikation verhindern.

## P0 – Direkt folgende technische Arbeiten

1. [ ] Schnelle SQLite-Suchschicht mit Pagination, Sortierung und kombinierbaren Filtern entwickeln.
2. [ ] FTS5-Index für Pfade, Namen und ausgewählte Textmetadaten entwickeln.
3. [ ] Ordneraggregate für Größe, Dateizahl, Typverteilung und Problemzahlen inkrementell pflegen.
4. [ ] Konsistente Prozesssperre auch für zukünftige schreibende Planungsoperationen erzwingen.
5. [ ] Sitzungsaufbewahrung und sichere Bereinigung alter Snapshots entwickeln.
6. [ ] Änderungsbericht pro Re-Scan als JSON, CSV und HTML ergänzen.

## P1 – Bedienung und Medienprüfung

7. [ ] Touchfähige PySide6-Oberfläche mit Einfach-, Geführt- und Expertenmodus entwickeln.
8. [ ] Bild-, Audio-, Video- und Textvorschau entwickeln.
9. [ ] FFmpeg/ffprobe und MediaInfo optional anbinden.
10. [ ] Beschädigte oder falsch benannte Medien erkennen.
11. [ ] Große Ordner und Speicherfresser visuell darstellen.
12. [ ] Suchprofile speichern, exportieren und importieren.

## P2 – Sichere Änderungsplanung

13. [ ] Unveränderliche Umbenennungspläne mit Vorher-Nachher-Vorschau entwickeln.
14. [ ] Zielkonflikt-, Rechte- und Speicherplatzprüfung entwickeln.
15. [ ] Transaktionsjournal für Kopieren, Verschieben und Umbenennen entwickeln.
16. [ ] Undo-Manifest und Quarantäne entwickeln.
17. [ ] Abbruch- und Recoverytests für jede schreibende Operation entwickeln.

## P3 – Qualität und Veröffentlichung

18. [ ] Ruff, MyPy, Bandit und pip-audit in CI integrieren.
19. [ ] Testabdeckung auf mindestens 80 Prozent erhöhen.
20. [ ] Lasttests mit mindestens einer Million Indexeinträgen durchführen.
21. [ ] Portables Linux-Paket mit Doppelklick-Starter entwickeln.
