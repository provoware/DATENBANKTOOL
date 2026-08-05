# Analyse-Punkte

Stand: Version `0.18.0-alpha.1`

## Gesamtergebnis dieser Iteration

| Bereich | Befund | Professionelle Korrektur |
|---|---|---|
| Wirkungsvorschau | Eine Sicherung ließ ihre konkrete Wirkung auf die aktive Datei nicht sicher erkennen | rein lesender Vergleich mit Hinzufügen, Entfernen, Ersetzen und Unverändert |
| Zuordnung | Ein beliebiger JSON-Pfad könnte der falschen Konfigurationsart zugeordnet werden | ausschließlich frischer Katalogeintrag plus unterstütztes Such-/Zeitreihen-Dateinamensmuster |
| Sicherungszustand | Syntaktisch vorhandene Datei war nicht automatisch wiederherstellbar | nur grüner Gesundheitsstatus und vollständige fachliche Deserialisierung |
| Mehrdeutige Namen | Doppelte Vorlagennamen könnten den Vergleich verfälschen | case-insensitive Eindeutigkeitsprüfung vor jeder Freigabe |
| Veralteter Vergleich | Aktive Datei oder Sicherung könnte sich nach der Vorschau ändern | erneuter SHA-256-Abgleich unmittelbar vor der Mutation |
| Rückfallsicherheit | Überschreiben ohne neuen Ausgangspunkt erschwerte eine sichere Rückkehr | automatische geprüfte Rückfallsicherung unmittelbar vor dem Restore |
| Veröffentlichung | Teilweise geschriebene Konfiguration wäre unbrauchbar | atomare Veröffentlichung mit Modus `0600`, Datei- und Ordner-`fsync` |
| Nachprüfung | Erfolgreicher Schreibaufruf beweist keinen gültigen Inhalt | bytegenaue SHA-256- und vollständige Schema-/Vorlagenprüfung |
| Fehler nach Mutation | Fehlgeschlagene Nachprüfung könnte die aktive Datei im falschen Stand lassen | automatisches Rückspielen und erneutes Prüfen der Rückfallsicherung |
| Nutzerentscheidung | Eine einzelne Ja/Nein-Frage wäre für eine weitreichende Änderung zu schwach | exakter Sicherungsname, sichtbare Argumentliste und `--yes` |
| Unnötige Mutation | Identische Datei könnte ohne Nutzen neu geschrieben werden | bytegenaue Identität führt kontrolliert zu keiner Änderung |
| Aufbewahrung | Komfortautomatik könnte wichtige Rückfallstände löschen | keine Auswahl-, Rotations-, Sammel- oder Altersautomatik |
| Architektur | Vergleich und Restore benötigten eine eigene Vertrauensgrenze | Fachlogik in `core/config_restore.py`, CLI nur Parser und Darstellung |
| Testrealismus | Erfolgspfad allein deckt den kritischsten Fehler nicht ab | simulierte fehlgeschlagene Nachprüfung mit bestätigtem automatischem Rückfall |

## Automatisch geprüfte Verträge

1. Suchvorlagen-Vergleich meldet Hinzufügen, Entfernen und Ersetzen korrekt.
2. Zeitreihen-Sicherung wird ausschließlich der Zeitreihen-Konfiguration zugeordnet.
3. Vergleich verändert weder Sicherung noch aktive Datei.
4. Wiederherstellung erstellt eine bytegenaue Rückfallsicherung des vorherigen aktiven Stands.
5. Ausgewählte Sicherung und Rückfallsicherung bleiben erhalten.
6. Aktive Datei und Rückfallsicherung besitzen Dateimodus `0600`.
7. Fehlendes `--yes` wird abgelehnt.
8. Falsch wiederholter Dateiname wird abgelehnt.
9. Bereits identische Dateien werden nicht erneut überschrieben oder gesichert.
10. Unbekannte, beschädigte und Indexsicherungen werden abgelehnt.
11. Eine simulierte fehlgeschlagene Nachprüfung setzt die aktive Datei automatisch zurück.
12. CLI-Vergleich und Restore liefern stabile JSON-Strukturen.
13. Die geführte Startseite zeigt die Wirkung und dispatcht exakt die sichtbare Argumentliste.
14. Eine falsche Namenswiederholung führt zu keinem Dispatch.
15. Parser, Handler, `CommandPolicy`, Modulzuständigkeit und Shellverbot bleiben konsistent.
16. 139 Tests laufen unter Python 3.10 und 3.12 mit Warnungen als Fehler.
17. Quick- und Standardabnahme bestehen jeweils 11/11 Kriterien.

## Wartbarkeitsentscheidung

- Katalogisierung und Gesundheitsstatus bleiben in `core/backup_catalog.py`.
- Vorsicherungen bleiben in `core/config_backups.py`.
- Vergleich, Restore, Prüfsummen, Rückfallsicherung und automatischer Rückfall liegen zusammen in `core/config_restore.py`.
- `cli_backups.py` registriert die öffentlichen Befehle und formatiert Terminal/JSON.
- `core/terminal_home.py` zeigt den Vergleich und baut ausschließlich sichere Argumentlisten.
- Bestehende Such- und Zeitreihen-Deserialisierung dient als fachliche Validierung; keine zweite Schemaimplementierung.
- Keine neue Laufzeitabhängigkeit.
- Keine Änderung der Originaldatei-Sperre.

## Nächste Analysepunkte

1. Rein lesenden Terminal-/JSON-Diagnosebefehl für alle Wiederanlaufeinträge entwerfen.
2. Optionales manipulationsarmes Wiederherstellungsprotokoll mit Pfaden, UTC und Prüfsummen definieren.
3. Reale Laienabnahme für Vergleich, Namensbestätigung und Rückfallverständnis durchführen.
4. Datenträger-voll- und Prozessabbruchtests ausschließlich mit synthetischen Konfigurationen dokumentieren.
