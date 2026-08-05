# Analyse-Punkte

Stand: Version `0.17.0-alpha.1`

## Gesamtergebnis dieser Iteration

| Bereich | Befund | Professionelle Korrektur |
|---|---|---|
| Wiederanlaufdaten | Ein einzelner Marker verdrängte unterbrochene Scans anderer Indexdateien | Schema 2 mit begrenzter Liste und einem Eintrag je normalisierter Indexdatei |
| Listenwachstum | Unbegrenzte Statusdaten könnten dauerhaft anwachsen | festes Limit von zwölf Einträgen; nur ältester interner Hinweis fällt aus der Liste |
| Gleichzeitige Zugriffe | Parallele Prozesse könnten dieselbe JSON-Datei aktualisieren | lokale `fcntl`-Dateisperre plus atomare private Veröffentlichung |
| Deduplizierung | Derselbe Index könnte mehrfach erscheinen | SHA-256-Kennung aus normalisiertem Datenbankpfad; neuer Stand ersetzt nur diesen Eintrag |
| Vertrauensgrenze | Ein gespeicherter Befehl allein belegt keine Startbarkeit | jeder Eintrag wird getrennt gegen Ordner, Index, Scanart, Stammordner und SQLite-Sitzung geprüft |
| Fehlende Datenträger | Nicht eingehängte Ordner dürfen weder verschwinden noch gestartet werden | als nicht startbar sichtbar halten; Entfernung nur nach bewusster Einzelentscheidung |
| Laienbedienung | Mehrere Kandidaten benötigten eindeutige Auswahl | nummerierte Übersicht, Detailansicht, genau ein Start-/Erhalten-/Verwerfen-Dialog |
| Erfolgsbereinigung | Ein erfolgreicher Lauf durfte andere Hinweise nicht entfernen | Entfernung ausschließlich anhand der Eintragskennung der betroffenen Indexdatei |
| Vorlagenrisiko | Ersetzen oder Löschen konnte ohne Rückfallkopie erfolgen | optionale geprüfte JSON-Sicherung vor der eigentlichen Änderung |
| Sicherungsvertrauen | Eine kopierte Datei könnte unvollständig oder strukturell defekt sein | Quelle und Ziel auf UTF-8-JSON, Objekt, Schema, Vorlagenliste, Inhalt und SHA-256 prüfen |
| Fehlerreihenfolge | Vorlagenänderung durfte bei Sicherungsfehler nicht weiterlaufen | Sicherung vollständig abschließen, erst danach Mutation ausführen |
| Rotation | Komfortfunktion könnte alte Sicherungen unbemerkt löschen | keinerlei automatische Rotation, Alterslöschung oder Sammellöschung |
| Architektur | Sicherungsoption ließ zwei CLI-Module anwachsen und duplizierte Darstellung | gemeinsamer kleiner Helfer `cli_preset_change.py`; Kompatibilitätsmodul ohne zweite Implementierung |
| Modulgrenze | `cli_search.py` überschritt vorübergehend 500 Zeilen | Hilfslogik ausgelagert; verbindlicher Architekturtest wieder grün |

## Automatisch geprüfte Verträge

1. Zwei verschiedene Indexdateien bleiben gleichzeitig gespeichert und getrennt validiert.
2. Erfolgreiche Fortsetzung entfernt nur den eigenen Eintrag.
3. Derselbe Datenbankpfad wird dedupliziert und enthält genau ein `--resume`.
4. Die Liste bleibt auf zwölf Einträge begrenzt, ohne Indexdateien anzutasten.
5. Bewusstes Verwerfen entfernt nur den ausgewählten Eintrag.
6. Fehlende Ordner oder Datenbanken bleiben sichtbar und werden nicht gestartet.
7. Suchvorlagen-Ersetzen sichert den unveränderten alten Inhalt.
8. Zeitreihen-Vorlagen-Löschen sichert die bisherige Vorlage.
9. Ohne Option entsteht keine Sicherung.
10. Mehrere ausdrücklich erzeugte Sicherungen bleiben vollständig erhalten.
11. Beschädigtes JSON wird nicht als Sicherung freigegeben.
12. Neue Konfigurationssicherungen erscheinen grün im Sicherungskatalog.
13. Alle CLI-Module bleiben innerhalb der Größenlimits.
14. 130 Tests laufen unter Python 3.10 und Python 3.12 mit Warnungen als Fehler.
15. Quick- und Standardabnahme bestehen jeweils 11/11 Kriterien.

## Wartbarkeitsentscheidung

- Persistenz und Sperre liegen in `core/run_journal.py`.
- Fachliche Einzelvalidierung liegt in `core/recovery.py`.
- Dialogauswahl liegt in `core/terminal_home.py` und führt nur Argumentlisten aus.
- Konfigurationskopie und Nachprüfung liegen in `core/config_backups.py`.
- Gemeinsame CLI-Option und Ausgabe liegen in `cli_preset_change.py`.
- Keine neue Laufzeitabhängigkeit.
- Keine automatische Originaldateioperation.

## Nächste Analysepunkte

1. Rein lesenden Terminal-/JSON-Diagnosebefehl für alle Wiederanlaufeinträge entwerfen.
2. Geführte Wiederherstellung einer ausgewählten Konfigurationssicherung mit Rückfallsicherung definieren.
3. Reale Laienabnahme mit zwei unterbrochenen Indexdateien durchführen.
4. Neustart-, Datenträger-ausgehängt- und Fast-voll-Test mit synthetischen Daten dokumentieren.
