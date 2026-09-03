# Entwicklungsdisziplin · gezielte Patches

## Ziel

Änderungen sollen klein, nachvollziehbar und wiederverwendbar bleiben. Vor dem ersten Patch wird immer geklärt, wo die Ursache liegt und welche Datei tatsächlich verantwortlich ist.

## Pflichtablauf

1. **Gate prüfen** – aktueller `main`-Head und seine CI-/Release-Gates müssen bekannt sein.
2. **Ort bestimmen** – betroffene Schicht, Datei, Funktion und Abhängigkeiten grob eingrenzen.
3. **Wiederverwendung suchen** – vorhandene Registry, Helfer, Tokens und Verträge zuerst prüfen.
4. **Patch-Grenze festlegen** – kleinsten ursachengerechten Änderungsschnitt notieren.
5. **Ändern** – keine parallele zweite Lösung einführen.
6. **Regressiv prüfen** – Formatter, Tests, Projektprüfer und fachliche Regressionen ausführen.
7. **Diff auditieren** – nur erwartete Dateien dürfen im Branch-Diff stehen.
8. **PR-Gate** – PR erst nach grünem Branch-CI; Merge erst nach grünem PR-CI.
9. **Main-Gate** – CI und Release Gate auf exakt dem Merge-Head erneut prüfen.

## Voranalyse-Notiz pro Änderung

Vor Codeänderungen werden mindestens diese Punkte festgehalten:

- Ziel / Fehlerbild
- vermutete Ursache
- ungefähre Code-Orte
- betroffene Verträge und Daten
- vorhandene wiederverwendbare Funktion oder Komponente
- kleinster geplanter Patch
- erwartete Regressionstests

## Versionierungsvertrag

`VERSION.json` ist die kanonische Übersicht der Produkt-, Schema- und Vertragsversionen.

- **Produktversion**: sichtbarer Entwicklungsstand.
- **Schema-Version**: Aufbau eines gespeicherten Formats.
- **Vertragsversion**: Verhalten eines Sicherheits- oder API-Vertrags.
- **Registry-Version**: Aufbau der zentralen Registry.
- **Sprachkatalog-Version**: Aufbau der ausgelagerten UI-Texte.

Eine interne Schemaänderung erzwingt nicht automatisch eine Produkt-Hauptversion. Bereits veröffentlichte Schema- oder Migrationsstände werden niemals still umgedeutet.

## Registry-Regel

`src/config/registry.json` ist der Index für stabile technische IDs, Module, API-Endpunkte, Fehlercodes und zentrale Querschnittspfade. Neue Funktionen prüfen zuerst, ob eine passende Registry-ID oder bestehende Implementierung vorhanden ist.

## UI-Regel

Wiederkehrende Abstände, Radien, Schatten und semantische Farben werden als CSS-Variablen geführt. Neue Komponenten verwenden diese Tokens statt neue Einzelwerte zu erfinden.

Sichtbare deutsche UI-Texte gehören in `src/web/i18n/de.json`. Logik enthält nur notwendige technische Fallbacks.

## Schutz bestehender Sicherheitskerne

Persistence-, Recovery-, Backup- und Restore-Verträge werden bei Wartbarkeitsarbeiten nicht nebenbei umgebaut. Änderungen an diesen Schichten benötigen einen eigenen fachlichen Grund und eigene Regressionen.
