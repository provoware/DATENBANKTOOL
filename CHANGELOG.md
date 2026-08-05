# Changelog

## 0.21.0-alpha.1 – 2026-08-05

### Geführte Protokollauswahl nach Restore

- Die Startseite fragt nach exakter Sicherungsnamensbestätigung optional nach einem neuen absoluten Protokollpfad.
- Nur eine ausdrückliche Eingabe ergänzt `--restore-log` zur sicheren Argumentliste.
- Leere Eingabe hält den bisherigen Restore-Befehl unverändert.
- Existierende Ziele und Symlinks werden vor der Befehlsfreigabe abgelehnt.
- Kein Zielvorschlag, keine automatische Auswahl, Benennung, Rotation oder Löschung.

### Geführte Protokollprüfung

- Neue Startseitenaktion `Protokoll prüfen` unter „Sicherungen verwalten“.
- Genau ein vollständiger Pfad wird normalisiert und vor der Befehlsbestätigung sichtbar angezeigt.
- Keine Datenbankauswahl, automatische Suche oder Dateiliste erforderlich.
- Die Aktion führt ausschließlich `index backups verify-log PROTOKOLL` als Argumentliste aus.
- Die bestehende Grün-/Gelb-/Rot-Auswertung und die Rückgabecodes bleiben unverändert.

### Optionaler Protokoll-SHA-Pin

- `verify-log` unterstützt `--expected-protocol-sha256`.
- Der erwartete Wert muss exakt 64 kleingeschriebene Hexzeichen enthalten.
- Die ausgewählte Protokolldatei wird vor jeder JSON-Schemaauswertung sicher und ohne Symlink-Folgen gehasht.
- Bei Abweichung endet der Befehl fail-closed mit Code `2`; der Schema-Prüfer wird nicht aufgerufen.
- JSON enthält bei erfolgreichem Pin zusätzlich `protocol_identity`.
- Keine automatische Ermittlung, Speicherung oder Historie.

### Architektur und Prüfung

- Neue kleine Erweiterungsschicht `core/terminal_home_restore_audit.py`; bestehende große Startseitenklasse bleibt unverändert.
- Neues Nur-Lese-Modul `core/restore_audit_identity.py`.
- Keine neue Laufzeitabhängigkeit und keine Shell-Auswertung.
- 158 Tests unter Python 3.10 und 3.12; Quick- und Standardabnahme jeweils 11/11.

## 0.20.0-alpha.1 – 2026-08-05

- Rein lesender Prüfbefehl für Restore-Protokolle.
- Strikte Schema-, UTC-, Pfad- und SHA-256-Prüfung.
- Drei referenzierte Dateien werden sicher und gestreamt verglichen.

## 0.19.0-alpha.1 – 2026-08-05

- Rein lesende Wiederanlauf-Diagnose.
- Optionales inhaltsfreies Wiederherstellungsprotokoll.

## 0.18.0-alpha.1 – 2026-08-05

- Geführte Konfigurations-Wiederherstellung mit automatischer Rückfallsicherung und Nachprüfung.

## 0.17.0-alpha.1 – 2026-08-05

- Begrenzte Mehrfach-Wiederanläufe und optionale Vorsicherungen vor Vorlagenänderungen.

## Frühere Entwicklungsstufen

- **0.1–0.16:** Scanner, SQLite-Index, Re-Scan, Suche, Berichte, Zeitreihen, Vorlagen, Hilfesystem, Crash-Sicherheit und Sicherungskatalog.
