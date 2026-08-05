# Analyse-Punkte

Stand: Version `0.16.0-alpha.1`

## Gesamtergebnis dieser Iteration

| Bereich | Befund | Professionelle Korrektur |
|---|---|---|
| Wiederanlaufdaten | Das allgemeine Laufjournal kannte auf der Startseite nicht sicher den inneren Scanbefehl | eigener `resume-run.json`-Datensatz für bestätigte Vollscans und Re-Scans |
| Vertrauensgrenze | Ein gespeicherter Befehl könnte veraltet oder unvollständig sein | Ordner, Datenbank, Scanart und SQLite-Sitzung werden vor Anzeige nur lesend validiert |
| Laienbedienung | `--resume` musste manuell ergänzt werden | vollständiger Befehl wird vorausgefüllt, sichtbar angezeigt und erst nach Ja gestartet |
| Ablehnung | Ein abgelehnter Wiederanlauf durfte nicht verloren gehen | Nein, q und geschlossene Eingabe erhalten den Hinweis für später |
| Stale State | Ein alter Marker könnte dauerhaft irreführen | fehlt die passende fortsetzbare SQLite-Sitzung, wird nur der interne Marker entfernt |
| Sicherungsfindung | Nutzer mussten Sicherungsdateien selbst im Dateisystem unterscheiden | Katalog mit Typ, Alter, Größe, Pfad, Status und technischer Begründung |
| Indexprüfung | Dateiendung allein belegt keine nutzbare Sicherung | SQLite `mode=ro`, `query_only`, `quick_check` und Schemaversion |
| Konfigurationsprüfung | JSON-Datei konnte syntaktisch oder strukturell defekt sein | JSON-Objekt, `schema_version` und `presets`-Liste werden geprüft |
| Löschsicherheit | Eine allgemeine Pfadlöschung wäre zu weitreichend | ausschließlich katalogisierte Einzelfile, exakter Name, `--yes`, abschließendes Ordner-`fsync` |
| Symlink-Risiko | `resolve()` im zentralen Löschhelfer hätte einen Symlink bis zum Ziel verfolgen können | lexikalische Absolutnormalisierung; Symlink-Ziele werden zentral bei Schreiben und Löschen abgelehnt |
| Wartbarkeit | Sicherungssortierung verwendete negative Werte plus `reverse=True` | direkte Sortierung nach Alter, neueste Sicherung zuerst |
| Architektur | Neue öffentliche Befehle benötigten Seiteneffekt- und Modulvertrag | `cli_backups.py`, Policies und Eigentümertests ergänzt |

## Automatisch geprüfte Verträge

1. Vollscan-Wiederanlauf wird erkannt und erhält genau ein `--resume`.
2. Inkrementeller Re-Scan wird getrennt als Änderungsprüfung erkannt.
3. Ablehnen führt keinen Befehl aus und erhält den Wiederanlaufdatensatz.
4. Bestätigen führt exakt die sichtbare Argumentliste aus.
5. Erfolgreicher Scan entfernt nur den Wiederanlaufhinweis.
6. Veralteter Marker ohne passende SQLite-Sitzung wird bereinigt.
7. Gültige Index- und Konfigurationssicherungen werden grün bewertet.
8. Beschädigte JSON-Sicherung wird rot bewertet.
9. CLI-JSON-Ausgabe enthält stabile Felder.
10. Einzellöschung benötigt katalogisierten Pfad, exakten Namen und `--yes`.
11. Aktive Indexdatei kann nicht über den Sicherungskatalog gelöscht werden.
12. Symlink-Sicherung bleibt erhalten und ihr Ziel wird nicht verändert.
13. Zentrale atomare Schreibfunktion überschreibt kein Symlink-Ziel.
14. Zentrale dauerhafte Löschung folgt keinem Symlink.
15. Neue CLI-Befehle besitzen Handler, Policy und eindeutige Modulzuständigkeit.

## Wartbarkeitsentscheidung

- Wiederanlaufvalidierung liegt in `core/recovery.py`, nicht in der Dialogklasse.
- Sicherungsprüfung und Löschvertrag liegen in `core/backup_catalog.py`.
- Terminaldialog baut nur sichere Argumentlisten und führt keine Shell aus.
- Bestehender Backup-Befehl bleibt kompatibel.
- Keine neue Laufzeitabhängigkeit.
- Keine Freigabe automatischer Originaldateioperationen.

## Nächste Analysepunkte

1. Mehrere Wiederanlaufdatensätze verschiedener Indexdateien begrenzt und konfliktfrei verwalten.
2. Vorlagenänderungen optional mit zeitgestempelter Konfigurationssicherung verbinden.
3. Reale Laienabnahme mit Beobachtung der Ja/Nein-Entscheidungen durchführen.
4. Neustart- und fast-voller-Datenträger-Test mit synthetischen Daten dokumentieren.
