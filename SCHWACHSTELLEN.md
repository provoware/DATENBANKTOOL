# Schwachstellen und aktuelle Grenzen

## Kritisch vor Freigabe schreibender Funktionen

1. **Noch kein Transaktionsjournal** – Änderungen könnten nach Abbruch nicht sicher rekonstruiert werden.
2. **Noch kein Undo-Manifest** – Umbenennen, Verschieben und Löschen bleiben deshalb gesperrt.
3. **Noch keine Zielkonfliktprüfung** – Namenskollisionen und Dateisystemgrenzen sind noch nicht vollständig modelliert.
4. **Noch keine Quarantäne** – Direktlöschung darf nicht eingeführt werden.
5. **Noch kein persistenter Index** – sehr große Sammlungen müssen bei jedem Lauf neu gelesen werden.

## Hohe Priorität

6. Der Scanner ist synchron und noch nicht pausierbar.
7. Der aktuelle Bericht hält alle Datensätze im Arbeitsspeicher.
8. Mountwechsel und Bind-Mounts werden noch nicht gesondert erkannt.
9. Parallel veränderte Dateien können zwischen `stat` und Hashing abweichen.
10. Duplikaterkennung erkennt nur bitgenau gleiche Dateien, keine inhaltlich ähnlichen Medien.
11. Dateitypen werden bisher hauptsächlich über Endungen erkannt.
12. Es fehlen echte Medienintegritätsprüfungen über ffprobe oder MediaInfo.
13. Archive werden noch nicht inhaltlich inventarisiert.
14. Textinhalte und Kodierungen werden noch nicht geprüft.
15. Codeprojektgrenzen und Buildreste werden noch nicht erkannt.

## Bedienung

16. Noch keine grafische Oberfläche.
17. Noch keine Touch- und Mobilansicht.
18. Noch keine Vorschau für Medien und Texte.
19. Noch keine geführten Assistenten für Laien.
20. Fehlermeldungen der CLI sind funktional, aber noch nicht vollständig kategorisiert.

## Qualität

21. Basisprüfungen sind vorhanden, aber Coverage-Grenze fehlt.
22. Ruff, MyPy, Bandit und pip-audit sind konfiguriert beziehungsweise vorgesehen, aber noch nicht als CI-Gate aktiv.
23. Tests auf echten großen Datenträgern, NTFS, exFAT und schreibgeschützten Medien fehlen.
24. Lasttests mit Millionen Dateien fehlen.
25. Paketierung und Doppelklick-Start fehlen.

## Sicherheitsfazit

Der aktuelle Stand ist als rein lesender Analyse-Prototyp vertretbar. Er ist ausdrücklich noch nicht für produktive Dateiänderungen freigegeben. Schreibende Funktionen dürfen erst nach vollständig geprüfter Vorschau-, Journal-, Konflikt-, Undo- und Wiederherstellungslogik aktiviert werden.
