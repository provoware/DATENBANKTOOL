# Upgrade-Pool

## Hoher Nutzen, geringes Risiko

1. Inkrementellen Re-Scan auf Basis von Pfad, Größe und Änderungszeit ergänzen.
2. `index sessions` zur Anzeige aller Sitzungen ergänzen.
3. `index backup` und `index restore` als getrennte Kommandos ergänzen.
4. gespeicherte Berichtsfilter als JSON-Profile einführen.
5. CSV-Trennzeichen und Excel-kompatible Profile auswählbar machen.
6. HTML-Berichte nach Größe automatisch in mehrere Seiten teilen.
7. Statistikbericht nach Kategorie, Größenklasse und Warncode ergänzen.
8. Suchkommando für den SQLite-Index ergänzen.
9. Fortschrittsausgabe als JSON Lines für spätere GUI-Anbindung ergänzen.
10. Logdatei mit rotierender Größenbegrenzung ergänzen.

## Mittlerer Aufwand

11. FTS5 für Dateinamen und Pfade.
12. Freigegebene Textinhalte mit Datenschutzprofil indizieren.
13. Dateiidentität über Gerät und Inode speichern.
14. externe Datenträger über stabile Kennung wiedererkennen.
15. Änderungsabgleich zwischen zwei Sitzungen darstellen.
16. verwaiste und entfernte Dateien markieren.
17. Hashcache sitzungsübergreifend wiederverwenden.
18. BLAKE3 optional für schnelle Vorprüfung evaluieren; SHA-256 bleibt Beweiswert.
19. PySide6-Such- und Filteroberfläche.
20. Auftragspause und Fortsetzung über UI.

## Medienfokus

21. ffprobe-Metadaten.
22. Audio-Wellenform und Vorhörfunktion.
23. Video-Vorschaubild und technische Prüfung.
24. Bildabmessungen und EXIF-Metadaten.
25. PDF- und Textvorschau in abgesichertem Modus.
26. Audio-Fingerprints.
27. perceptual Hash für Bilder.
28. beschädigte Container erkennen.
29. falsche Dateiendungen erkennen.
30. Begleitdateien, Untertitel und Playlists gruppieren.

## Später, erst nach Sicherheitskern

31. unveränderliche Umbenennungspläne.
32. Vorher-Nachher-Vorschau.
33. Kollisionsprüfung.
34. transaktionales Dateioperationsjournal.
35. Undo-Manifest.
36. Quarantäne statt Direktlöschung.
37. Wiederaufnahme halbfertiger Dateioperationen.
38. Wiederherstellungstest vor Freigabe.
39. Geräteübergreifende Kopierprüfung.
40. Stable-Release-Gate für schreibende Funktionen.
