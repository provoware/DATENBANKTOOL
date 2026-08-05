# Analyse-Punkte

Stand: Version `0.20.0-alpha.1`

## Gesamtergebnis dieser Iteration

| Bereich | Befund | Professionelle Korrektur |
|---|---|---|
| Spätere Nachprüfung | Restore-Protokoll wurde beim Erzeugen bestätigt, aber später nicht erneut gegen Dateien geprüft | eigener Befehl `index backups verify-log PROTOKOLL` |
| Dateiauswahl | Automatische Suche könnte den falschen Nachweis auswählen | ausschließlich ausdrücklich übergebener Protokollpfad |
| Schema-Drift | Zusätzliche, fehlende oder umbenannte Felder könnten unbemerkt bleiben | exakter Schlüsselsatz für oberste Ebene und SHA-256-Objekt |
| Zeitqualität | Beliebige Zeittexte oder lokale Offsets wären nicht eindeutig | ISO-8601-Parsing, Pflicht-UTC und logische Reihenfolge |
| Pfadqualität | Relative oder doppelte Pfade machen den Nachweis uneindeutig | genau drei unterschiedliche absolute Pfade |
| Hashqualität | Falsche Länge, Rolle oder Schreibweise könnte als Prüfsumme erscheinen | exakt drei Rollen und 64 kleingeschriebene Hexzeichen |
| Symlink-Risiko | Prüfen könnte auf ein anderes Ziel umgelenkt werden | `O_NOFOLLOW`, normale Datei per `fstat`, keine Auflösung |
| Speicherbedarf | Große Referenzdateien vollständig einzulesen wäre unnötig | SHA-256 in 1-MiB-Blöcken streamen |
| Ergebnisdeutung | Fehlende und abweichende Datei haben unterschiedliche Bedeutung | Gelb für fehlend, Rot für Abweichung oder unsicheren Zugriff |
| Seiteneffekte | Ein Prüfbefehl darf keinen Restore oder Reparaturversuch auslösen | reine `CommandPolicy`, kein Schreib-, Lösch- oder Restore-Handler |
| Maschinenlesbarkeit | Automatisierung braucht stabile Einzelzustände | JSON mit Status, Soll-/Ist-Hash, Zählern und `all_files_match` |
| Wartbarkeit | Sicherungs-CLI war bereits umfangreich | eigener Parser und Handler in `cli_restore_audit.py` |

## Automatisch geprüfte Verträge

1. Gültiges Schema mit drei vorhandenen Dateien ergibt Grün und Rückgabecode 0.
2. Alle drei tatsächlichen SHA-256-Werte stimmen mit den protokollierten Rollen überein.
3. Protokoll und referenzierte Dateien bleiben bytegenau unverändert.
4. Die Prüfung erzeugt keine neue Datei und entfernt keinen Pfad.
5. Veränderter aktiver Stand wird als rote Hashabweichung erkannt.
6. Fehlende ausgewählte Sicherung wird gelb als unvollständiger Nachweis gemeldet.
7. Zusatzfelder im Protokoll werden abgelehnt.
8. Nicht-UTC-Zeit und unlogische Zeitreihenfolge werden abgelehnt.
9. Relative und doppelte Pfade werden abgelehnt.
10. Fehlende Hashrolle und großgeschriebener Hash werden abgelehnt.
11. Protokoll-Symlink wird abgelehnt und nicht verfolgt.
12. Terminal nennt ausdrücklich die rein lesende Wirkung.
13. JSON enthält keine ANSI-Sequenzen und genau drei Dateiobjekte.
14. Hashabweichung liefert maschinenlesbar Rückgabecode 1.
15. Parser, Handler und rein lesende Policy sind korrekt gebunden.
16. CLI-Modulgrenzen, Größenlimits und Shellverbot bleiben eingehalten.
17. 151 Tests laufen unter Python 3.10 und 3.12 mit Warnungen als Fehler.
18. Quick- und Standardabnahme bestehen jeweils 11/11 Kriterien.

## Wartbarkeitsentscheidung

- Protokollerzeugung und -prüfung teilen das feste Schema in `core/restore_audit.py`.
- Lesen normaler Dateien ohne Symlink-Folgen ist eine gemeinsame interne Hilfsgrenze.
- `cli_restore_audit.py` enthält nur Parser, Ampeldarstellung, JSON und Rückgabecode.
- `cli_backups.py` registriert das Fachmodul, enthält aber keine zweite Prüflogik.
- Ungültiges Schema wird vor dem Zugriff auf protokollierte Dateipfade abgelehnt.
- Fehlende Dateien sind Ergebnisdaten und keine Ausnahme.
- Keine neue Laufzeitabhängigkeit.
- Keine Änderung der Originaldatei-Sperre.

## Nächste Analysepunkte

1. Rein lesende Protokollprüfung in die geführte Startseite integrieren.
2. Optionalen erwarteten SHA-256-Wert für die Protokolldatei als Identitäts-Pin definieren.
3. Reale Laienabnahme für Grün/Gelb/Rot und Soll-/Ist-Hash durchführen.
4. Große synthetische Referenzdatei und ausgehängten Datenträger auf dem Kubuntu-Zielsystem prüfen.
