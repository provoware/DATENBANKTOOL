# Analyse-Punkte

Stand: Version `0.21.0-alpha.1`

## Gesamtergebnis dieser Iteration

| Bereich | Befund | Professionelle Korrektur |
|---|---|---|
| Geführter Restore | CLI konnte ein Protokoll schreiben, Startseite aber keinen optionalen Zielpfad erfassen | kleine Erweiterungsschicht fragt erst nach exakter Sicherungsnamensbestätigung optional nach einem neuen Pfad |
| Leere Eingabe | Optionalität musste ohne versteckten Standardwert erhalten bleiben | leer lässt die sichere Restore-Argumentliste vollständig unverändert |
| Zielschutz | Vorhandene Datei oder Symlink darf nicht in einen später scheiternden Überschreibversuch gelangen | Ziel vor Befehlsfreigabe normalisieren, sichtbar anzeigen und bei Existenz/Symlink ablehnen |
| Automatikrisiko | Ein vorgeschlagener Zielpfad könnte unbeabsichtigte Dateien erzeugen | kein Vorschlag, keine Suche, keine automatische Benennung oder Speicherung |
| Geführte Prüfung | `verify-log` war nur über technische CLI erreichbar | eigene Aktion „Protokoll prüfen“ unter „Sicherungen verwalten“ |
| Unnötige Eingaben | Protokollprüfung benötigt keine Indexdatei | direkter Pfaddialog ohne Datenbankabfrage |
| Transparenz | Nutzer muss exakt sehen, welche Datei geprüft wird | normalisierten vollständigen Protokollpfad vor der finalen Befehlsbestätigung ausgeben |
| Identität | Gültiges Schema allein beweist nicht, dass die erwartete Protokolldatei gewählt wurde | optionaler expliziter SHA-256-Pin |
| Prüfungsreihenfolge | Ein falsches Protokoll darf nicht erst nach JSON-Auswertung auffallen | sichere Hashprüfung vor Decoding und Schema-Prüfer |
| Pinformat | Flexible Hashdarstellung wäre mehrdeutig | exakt 64 kleingeschriebene Hexzeichen |
| Datenschutz | Automatische Pin-Ermittlung oder Historie würde neue Metadaten erzeugen | Pin ausschließlich aus aktueller ausdrücklicher Eingabe verwenden |
| Wartbarkeit | Bestehende Startseitenklasse ist bereits umfangreich | neue Funktionen in `terminal_home_restore_audit.py` kapseln und über Entry-Point aktivieren |
| Lesesicherheit | Pinprüfung darf Symlinks oder Sonderdateien nicht akzeptieren | `O_RDONLY`, `O_CLOEXEC`, `O_NOFOLLOW`, `fstat()` und Streaming-Hashing |

## Automatisch geprüfte Verträge

1. Ausdrücklicher neuer Restore-Protokollpfad wird exakt als `--restore-log` angehängt.
2. Leere Eingabe ergänzt kein Argument.
3. Vorhandenes Ziel bleibt bytegenau unverändert und wird nicht angehängt.
4. Geführte Protokollprüfung verlangt keine Indexdatei.
5. Vollständiger Protokollpfad wird sichtbar ausgegeben.
6. Geführte Prüfung kann den Pin ausdrücklich setzen oder überspringen.
7. Richtiger Pin wird in Terminal und JSON bestätigt.
8. Falscher Pin liefert Code `2`.
9. Ungültiges Pinformat liefert Code `2`.
10. Bei falschem oder ungültigem Pin wird der Schema-Prüfer nicht aufgerufen.
11. Protokoll und drei Referenzdateien bleiben bei erfolgreicher Pinprüfung bytegenau unverändert.
12. Keine zusätzliche Laufzeitabhängigkeit oder Shell-Auswertung.
13. 158 Tests laufen unter Python 3.10 und 3.12 mit Warnungen als Fehler.
14. Quick- und Standardabnahme bestehen jeweils 11/11 Kriterien.

## Architekturentscheidung

- `core/terminal_home.py` bleibt unverändert und enthält weiterhin die bestehenden Recovery- und Sicherungsabläufe.
- `core/terminal_home_restore_audit.py` erweitert ausschließlich Backup-Aktionswahl, optionalen Restore-Protokollpfad und geführte Protokollprüfung.
- Der Entry-Point verwendet die Erweiterungsklasse; bestehende Basistests bleiben weiterhin gültig.
- `core/restore_audit_identity.py` enthält nur Pinformat, sichere Dateileseöffnung und SHA-256-Identitätsprüfung.
- `cli_restore_audit.py` steuert die Reihenfolge: optionaler Pin zuerst, bestehender Schema- und Dateiprüfer danach.
- Der Restore-Kern, die Protokollerzeugung und die drei Dateivergleiche bleiben unverändert.

## Nächste Analysepunkte

1. Geführte synthetische Kubuntu-Abnahmesitzung zur Schließung des letzten Hauptpunkts definieren.
2. Optionalen Prüfberichtsexport mit neuem nicht überschreibbarem Zielpfad untersuchen.
3. Ampelverständnis, leere optionale Eingabe und falschen Pin mit einer unerfahrenen Testperson beobachten.
4. Reale ext4- und USB-Zielpfade ausschließlich mit synthetischen Dateien prüfen.
