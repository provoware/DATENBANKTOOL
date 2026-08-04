# Schwachstellen

## Aktuelle technische Grenzen

1. **Checkpointdatei entfernt:** Wiederaufnahme bricht kontrolliert ab, wenn der gespeicherte Pfad nicht mehr auffindbar ist.
2. **Kein inkrementeller Re-Scan:** Abgeschlossene Sitzungen werden noch nicht differenziell aktualisiert.
3. **Kein Prozesslock:** Zwei parallele Indexprozesse können konkurrieren; SQLite schützt Transaktionen, aber nicht die fachliche Sitzungsauswahl.
4. **Keine Hash-Pause:** Hashing kann nach Prozessabbruch fortgesetzt werden, besitzt aber noch keinen Nutzerknopf für Pause.
5. **Fehlgeschlagener Hash wird nicht automatisch erneut versucht:** Der Fehler bleibt sichtbar; ein neuer Scan oder gezielte Reparaturstrategie ist nötig.
6. **WAL-Nebenwirkungen:** Lesen über den normalen Datenbankzugang kann SQLite-WAL-Dateien erzeugen.
7. **Reparaturgrenze:** Physisch stark beschädigte SQLite-Dateien können nicht garantiert geheilt werden.
8. **HTML-Skalierung:** Millionen Tabellenzeilen sind für eine einzelne Browserdatei ungeeignet.
9. **Keine Volltextsuche:** Der Index enthält derzeit Metadaten, keine Textinhalte.
10. **Keine Medienvalidierung:** Endungen werden klassifiziert; Codec, Container und tatsächlicher Inhalt werden noch nicht geprüft.
11. **Keine Dateisystemidentität:** Mountwechsel, Gerät und Inode werden noch nicht gespeichert.
12. **Keine automatische Sitzungslöschung:** Alte Sitzungen können die Datenbank langfristig vergrößern.
13. **Kein verschlüsselter Index:** Dateipfade liegen lokal im Klartext in der SQLite-Datenbank.
14. **Ruff/MyPy nicht ausgeführt:** Beide Werkzeuge waren in der lokalen Prüfungsumgebung nicht installiert.
15. **Noch keine reale Langzeitlastprüfung:** Tests verwenden kleine künstliche Bestände.

## Behobene Schwachstellen

1. Flüchtige Scanergebnisse ohne Persistenz.
2. Fehlende Schema-Versionierung.
3. Fehlende Migration.
4. Import ohne Batchgrenzen.
5. Kein Wiederaufnahmezustand.
6. Keine Datenbankreparatur.
7. Keine Sicherheitskopie vor Reparatur.
8. Keine CSV-/HTML-Berichte.
9. Keine Filter nach Typ, Größe, Namensproblemen und Duplikaten.
10. Potenziell halbfertige Mehrfachausgabe ohne Vorprüfung.

## Sicherheitsfazit

Der Index- und Berichtskern ist für Alpha-Nutzung belastbar und nicht destruktiv. Eine Freigabe für schreibende Dateioperationen wäre weiterhin verfrüht und bleibt blockiert.
