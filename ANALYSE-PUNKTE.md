# Analyse-Punkte

Stand: Version `0.19.0-alpha.1`

## Gesamtergebnis dieser Iteration

| Bereich | Befund | Professionelle Korrektur |
|---|---|---|
| Diagnosezugang | Mehrere Wiederanläufe waren außerhalb der Startseite nicht vollständig prüfbar | eigener Terminal- und JSON-Befehl `index recovery` |
| Diagnoseumfang | Ein grober Hinweis reichte für Ursachenanalyse und Dokumentation nicht | Prüfstatus, Ordner, Index, Sitzung, Zustand, Phase, Dateizahl, UTC und Startbarkeit gemeinsam ausgeben |
| Seiteneffekte | Ein Diagnosebefehl dürfte keinen Scan starten oder Hinweis entfernen | reine `CommandPolicy` ohne Schreibwirkung; kein Start-, Verwerfen- oder Löschhandler |
| Nachweis der Lesewirkung | Nur ein erklärender Text beweist keine Unverändertheit | Tests vergleichen Bytes von `resume-run.json` und Indexdatei vor und nach Diagnose |
| Maschinenlesbarkeit | Terminalfarben und Bedienhinweise erschweren Automatisierung | stabiles JSON-Schema ohne ANSI mit Summen und vollständiger Eintragsliste |
| Leerer Zustand | Fehlende Einträge könnten als Fehler missverstanden werden | erfolgreicher Nullbefund mit `record_count: 0` und leerer Liste |
| Restore-Nachvollziehbarkeit | Erfolgreiche Wiederherstellung war später nur über Dateien rekonstruierbar | optionales kleines JSON-Protokoll nach bestätigtem Restore |
| Datenminimierung | Ein allgemeines Protokoll könnte Konfigurationsinhalte oder Geheimnisse erfassen | festes Schema nur mit UTC-Zeiten, drei Pfaden und drei SHA-256-Werten |
| Explizite Entscheidung | Automatisches Protokollieren würde neue Dateien ohne Nutzerauftrag erzeugen | ausschließlich bei `--restore-log PFAD` |
| Zielschutz | Bestehende Nachweise könnten überschrieben werden | existierende Datei und Symlink ablehnen; kein `overwrite=True` |
| Veröffentlichungsqualität | Teilweise geschriebenes JSON wäre kein belastbarer Nachweis | atomare Veröffentlichung, Modus `0600`, erneutes Lesen und vollständiger Payload-Vergleich |
| Teilfehler | Nachweisfehler nach erfolgreichem Restore darf den bestätigten Konfigurationsstand nicht verfälschen | Restore erhalten, separater Protokollfehler mit Rückgabecode `1` und technischer Ursache |
| Aufbewahrung | Automatische Ablage oder Rotation könnte Pfade und Nachweise unkontrolliert vermehren oder löschen | keine Benennung, Auswahl, Rotation oder Löschung |
| Architektur | Diagnose und Nachweis brauchten klar getrennte Zuständigkeiten | `cli_recovery.py` für Darstellung, `core/restore_audit.py` für den Schreibvertrag |

## Automatisch geprüfte Verträge

1. Terminaldiagnose zeigt alle geforderten Felder eines fortsetzbaren Eintrags.
2. JSON-Diagnose enthält Schema, Summen und vollständige Eintragsdaten ohne ANSI.
3. Leere Wiederanlaufliste liefert Rückgabecode 0 und eine leere JSON-Liste.
4. Diagnose verändert die Wiederanlaufdatei bytegenau nicht.
5. Diagnose verändert die geprüfte SQLite-Indexdatei bytegenau nicht.
6. Öffentlicher Diagnosebefehl besitzt Handler und rein lesende `CommandPolicy`.
7. Optionales Restore-Protokoll wird erst nach erfolgreichem Restore erzeugt.
8. Protokoll besitzt Modus `0600` und gültiges UTF-8-JSON.
9. Protokoll enthält exakt die drei benannten SHA-256-Rollen.
10. Aktiver Restore-Hash und Hash der ausgewählten Sicherung stimmen überein.
11. Eingebauter Geheimniswert und Konfigurationsdatensätze erscheinen nicht im Protokoll.
12. Ohne `--restore-log` entsteht keine Protokolldatei und die bisherige JSON-Ausgabe bleibt kompatibel.
13. Ein vorhandenes Ziel wird nicht überschrieben.
14. Bei Protokollfehler bleibt die erfolgreich wiederhergestellte aktive Datei erhalten.
15. Teilfehler wird maschinenlesbar mit `restore_log_error` und Rückgabecode 1 ausgegeben.
16. Parser, Handler, `CommandPolicy`, Modulzuständigkeit, Größenlimits und Shellverbot bleiben konsistent.
17. 145 Tests laufen unter Python 3.10 und 3.12 mit Warnungen als Fehler.
18. Quick- und Standardabnahme bestehen jeweils 11/11 Kriterien.

## Wartbarkeitsentscheidung

- Speicherung und Sperre der Wiederanlaufliste verbleiben in `core/run_journal.py`.
- Unabhängige SQLite-Nur-Lese-Prüfung verbleibt in `core/recovery.py`.
- `cli_recovery.py` enthält ausschließlich Parser, Summen und Terminal-/JSON-Darstellung.
- Restore und automatischer Rückfall verbleiben unverändert in `core/config_restore.py`.
- `core/restore_audit.py` erhält ausschließlich das minimale Nachweisschema und den atomaren Schreibvertrag.
- `cli_backups.py` steuert die Reihenfolge: Restore zuerst bestätigen, optional danach Protokoll schreiben.
- Ein Protokollfehler wird nicht fälschlich als fehlgeschlagener Restore dargestellt.
- Keine neue Laufzeitabhängigkeit.
- Keine Änderung der Originaldatei-Sperre.

## Nächste Analysepunkte

1. Rein lesenden Prüfbefehl für eine ausdrücklich ausgewählte Restore-Protokolldatei definieren.
2. Optionalen neuen Protokollpfad in den geführten Restore-Ablauf integrieren, ohne automatische Zielwahl.
3. Reale Laienabnahme für Diagnosefelder, Startbarkeit und Teilfehlermeldung durchführen.
4. Ausgehängten Datenträger, vorhandenes Protokollziel und vollen Datenträger ausschließlich mit synthetischen Daten dokumentieren.
