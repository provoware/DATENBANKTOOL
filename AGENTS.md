# AGENTS.md · verbindliche Entwicklungsregeln

## 1. Grundprinzip

Änderungen folgen immer:

`Voranalyse → Code-Ort bestimmen → kleinster Patch → Formatierung → Tests → Regression → Diff-Audit → Doku → Status`

Vor der ersten Codeänderung müssen Ziel, vermutete Ursache, ungefähre Code-Orte,
Abhängigkeiten, vorhandene Wiederverwendung und erwartete Regressionen feststehen.

## 2. Schichtentrennung

- `src/` enthält Basistool-Code.
- `config/` enthält nur versionierbare Standardkonfiguration.
- `data/` enthält keine echten Nutzerdaten; nur README/Schemata/Beispiele.
- `logs/`, `runtime/`, `backups/` und lokale Nutzerkonfiguration werden ignoriert.
- Tests schreiben ausschließlich in temporäre Verzeichnisse.
- Persistence-, Recovery-, Backup- und Restore-Verträge werden nicht nebenbei refaktoriert.

## 3. Wiederverwendung und Registry

- Vor neuen Helfern, Endpunkten oder Komponenten zuerst `src/config/registry.json` prüfen.
- Stabile Module, API-Endpunkte und Fehlercodes erhalten eindeutige Registry-IDs.
- Keine zweite Implementierung anlegen, wenn ein vorhandener Vertrag erweitert werden kann.
- Querschnittslogik gehört in wiederverwendbare zentrale Helfer, nicht in Fachmodule.

## 4. Versionierung

`VERSION.json` ist die kanonische Übersicht für Produkt-, Schema- und Vertragsversionen.

- Produktversion beschreibt den sichtbaren Entwicklungsstand.
- Schema-Version beschreibt einen gespeicherten Aufbau.
- Vertragsversion beschreibt verbindliches Laufzeitverhalten.
- Bereits verwendete Schema-/Migrationsstände werden niemals still umgedeutet.
- Spiegelwerte in Manifest oder UI müssen durch Regressionen auf Parität geprüft werden.

## 5. Datei- und Zeilengrenzen

Die maschinenlesbaren Grenzwerte in `MANIFEST.json` sind verbindlich.
Neue Dateien dürfen harte Maximalwerte nicht überschreiten.
Wird eine Datei zu groß, wird sie modularisiert statt der Grenzwert angehoben.

## 6. Logging

- Maschinenformat: JSONL.
- Nutzerformat: kurze deutsche TXT-Zusammenfassung.
- Jeder Fehler erhält stabilen Code, Schweregrad, Kurzursache und Handlungstipp.
- Sensible Daten niemals absichtlich loggen.
- `password`, `token`, `secret`, `cookie`, `authorization`, `api_key`
  werden automatisch geschwärzt.

## 7. UI, Sprache und Design-Tokens

- deutsche einfache Sprache.
- sichtbare UI-Texte bevorzugt aus `src/web/i18n/de.json` beziehen.
- Fachwörter bei erster Verwendung kurz erklären.
- wiederkehrende Abstände, Radien, Schatten und Farben als CSS-Tokens führen.
- keine neue Einzelgröße erfinden, wenn ein passender Token existiert.
- Tooltips ergänzen, aber keine Pflichtinformation nur im Tooltip verstecken.
- Farbe niemals als einziges Bedeutungssignal verwenden.
- sichtbarer Tastaturfokus ist Pflicht.
- Mindestkontrast WCAG-orientiert.

## 8. Status

- 🟢 bestanden / fertig
- 🟡 Hinweis / in Arbeit
- 🔴 blockiert / Fehler
- 🟣 Information

## 9. Platzhalter

Unfertige Produktstellen müssen eindeutig als `PLACEHOLDER[PH-XXX]`
markiert und in `TODO.md` geführt werden.

## 10. Release

Kein `STABLE`, solange release-blockierende Tests offen sind.
Ein grüner Unit-Test ersetzt keine reale UI-/Plattform-Endabnahme.
Branch-CI, PR-CI und die Main-Gates müssen auf ihren jeweils exakten Heads grün sein.
