# AGENTS.md · verbindliche Entwicklungsregeln

## 1. Grundprinzip

Änderungen folgen immer:

`Analyse → kleine Änderung → Formatierung → Tests → Regression → Doku → Status`

## 2. Schichtentrennung

- `src/` enthält Basistool-Code.
- `config/` enthält nur versionierbare Standardkonfiguration.
- `data/` enthält keine echten Nutzerdaten; nur README/Schemata/Beispiele.
- `logs/`, `runtime/`, `backups/` und lokale Nutzerkonfiguration werden ignoriert.
- Tests schreiben ausschließlich in temporäre Verzeichnisse.

## 3. Datei- und Zeilengrenzen

Die maschinenlesbaren Grenzwerte in `MANIFEST.json` sind verbindlich.
Neue Dateien dürfen harte Maximalwerte nicht überschreiten.
Wird eine Datei zu groß, wird sie modularisiert statt der Grenzwert angehoben.

## 4. Logging

- Maschinenformat: JSONL.
- Nutzerformat: kurze deutsche TXT-Zusammenfassung.
- Jeder Fehler erhält stabilen Code, Schweregrad, Kurzursache und Handlungstipp.
- Sensible Daten niemals absichtlich loggen.
- `password`, `token`, `secret`, `cookie`, `authorization`, `api_key`
  werden automatisch geschwärzt.

## 5. UI

- deutsche einfache Sprache.
- Fachwörter bei erster Verwendung kurz erklären.
- Tooltips ergänzen, aber keine Pflichtinformation nur im Tooltip verstecken.
- Farbe niemals als einziges Bedeutungssignal verwenden.
- sichtbarer Tastaturfokus ist Pflicht.
- Mindestkontrast WCAG-orientiert.
- dunkle Basis, helle Schrift, semantische Akzentfarben.

## 6. Status

- 🟢 bestanden / fertig
- 🟡 Hinweis / in Arbeit
- 🔴 blockiert / Fehler
- 🟣 Information

## 7. Platzhalter

Unfertige Produktstellen müssen eindeutig als `PLACEHOLDER[PH-XXX]`
markiert und in `TODO.md` geführt werden.

## 8. Release

Kein `STABLE`, solange release-blockierende Tests offen sind.
Ein grüner Unit-Test ersetzt keine reale UI-/Plattform-Endabnahme.
