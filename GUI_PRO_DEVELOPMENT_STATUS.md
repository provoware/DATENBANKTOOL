# Profi-GUI-Entwicklung – iterativer Status

Stand: 2026-08-08

## Verbindliche Leitentscheidung

Das bestätigte Einzel-GUI bleibt die visuelle und strukturelle Referenz. Die GUI ist eine additive Schicht. Der bestehende CLI-, Index-, Recovery-, Restore- und Crash-Sicherheitskern wird nicht in GUI-Code verschoben und nicht aufgeweicht.

## Architekturfluss

```text
bestehender sicherer Kern / SQLite-Index
              ↓
       ReadOnlyIndexAdapter
              ↓
      GUI-Modelle / Presets
              ↓
 Vorschau / Testlabor / Assistenz
              ↓
          Desktop-GUI
```

Keine GUI-Schicht besitzt derzeit einen automatischen Originaldatei-Schreibpfad.

## Nummerierter Profi-Umbauplan

| Nr. | Bereich | Status | Nächste technische Vertiefung |
|---:|---|---|---|
| 1 | Designvertrag zentralisieren | ERLEDIGT | Tokens später aus einer Quelle generieren |
| 2 | Native Desktop-GUI separate Schicht | ERLEDIGT | Widgets weiter modularisieren |
| 3 | `datenbanktool gui` | ERLEDIGT | Startdiagnose und Capability-Check ergänzen |
| 4 | CLI/Headless unabhängig | ERLEDIGT | Regression dauerhaft im Gate halten |
| 5 | Navigation + Projektkontext | BASIS ERLEDIGT | echte Projekt-/Quellenauswahl nur lesend |
| 6 | KPI, Speicher, Last, Sicherheit | TEILWEISE | Live-Progress und Gerätewerte anbinden |
| 7 | Detail-/Listenworkspace | BASIS ERLEDIGT | Pagination, Filter, Sortierung, gespeicherte Ansichten |
| 8 | Duplikate + Umbenennung | BASIS ERLEDIGT | echte Gruppenansicht + Rename-Preview-Engine |
| 9 | Schnellmodi + editierbare Presets | KERN ERLEDIGT | persistenter lokaler Preset-Store mit Schema |
| 10 | Testordner + Sandbox | KERN ERLEDIGT | reale temporäre Sandbox mit ausschließlich synthetischen Kopien |
| 11 | Assistent Was/Warum/Nächster Schritt | KERN ERLEDIGT | Ereignisadapter + kontextsensitive Empfehlungen |
| 12 | Audit, Restzeit, Bericht, Transparenz | KERN ERLEDIGT | vorhandene Progress-Events rein lesend anbinden |
| 13 | Barrierefreiheit, Skalierung, Tastatur | VERTRAG ERLEDIGT | echte Keybindings, Fokusführung, UI-Skalierung |
| 14 | Reale Kubuntu-Abnahme | OFFEN | X11/Wayland, Skalierung 100/125/150 %, kleine/große Displays |

## Neu implementierte Profi-Schichten

### `gui_readonly.py`

- SQLite ausschließlich mit `mode=ro`.
- zusätzlich `PRAGMA query_only = ON`.
- keine Verwendung der schreibfähigen `IndexDatabase`-Klasse.
- KPI-Abfragen für Dateien, Größen, Warnungen, unbekannte und große Dateien.
- Duplikatgruppen und potenziell einsparbare Bytes.
- limitierte Detailzeilen für große Sammlungen.

### `gui_presets.py`

- sichere Standard-Presets für häufige Ordnungsaufgaben.
- Regeln sind explizit und prüfbar.
- Standard-Presets sind nicht destruktiv.
- editierbare Presets dürfen weder Aktionsklasse noch Sicherheitsflag heimlich ändern.

### `gui_testlab.py`

- definierter gemischter Musterbestand.
- Bilder, Videos, Audio, Dokumente, Archive, System- und Unklarfälle.
- absichtliches Duplikatpaar.
- vollautomatische In-Memory-Validierung.
- keinerlei Originaldateizugriff.

### `gui_assistant.py`

- deterministische Erklärungen statt freier stiller Automatik.
- Scanbefund wird in Klartext bewertet.
- Aktionen können mit Grund, Wirkung und Reversibilität protokolliert werden.
- nächste Schritte hängen vom tatsächlich erreichten Zustand ab.

### `gui_transparency.py`

- Fortschritt, Prozentwert, Rate und Restzeit getrennt modelliert.
- unbekannte Restzeit bleibt ausdrücklich unbekannt.
- Sicherheits-/Wirkungsbericht enthält geplante Aktionen, geschützte Elemente, Warnungen und Fehler.

### `gui_accessibility.py`

- Skalierungsvertrag 80 bis 200 Prozent.
- Tastaturaktionen als expliziter Vertrag.
- WCAG-orientierte Kontrastberechnung.
- Reduced-Motion als Standardannahme.

### `gui_quality.py`

Automatisches Gate für:

- alle Pflicht-Layoutzonen,
- gültige zentrale Farb-Tokens,
- unterscheidbare Signalzustände,
- Kontrast/Accessibility,
- sichtbare Sicherheitszustände,
- nicht-destruktive Presets,
- Mindestumfang des Detailworkspaces,
- verständliche nächste Schritte.

## Sicherheitsprinzipien für folgende Iterationen

1. Neue GUI-Datenquellen zuerst rein lesend anbinden.
2. Keine direkte Dateisystemänderung aus Widgets.
3. Vorschlag und Ausführung bleiben getrennte Zustände.
4. Jede geplante Änderung benötigt Vorher/Nachher-Darstellung.
5. Unsichere Klassifikation führt zu Vorschlag, niemals zu stiller Aktion.
6. Fehlerhafte oder unbekannte Elemente werden standardmäßig übersprungen und sichtbar protokolliert.
7. Listen für große Sammlungen werden begrenzt/paginiert, niemals unkontrolliert komplett gerendert.
8. Restzeiten werden nur bei belastbarer Rate angezeigt.
9. Der Assistent erklärt Fakten und Vorschläge; er erfindet keine Dateiinhalte.
10. Reale Schreibfunktionen dürfen erst nach eigenem Transaktions-, Papierkorb-, Undo- und Recovery-Vertrag folgen.

## Direkt folgende Entwicklungswelle

### GUI-003 – Search/Filter/Pagination ViewModel

- serverseitige SQLite-Filter statt Millionen Zeilen im RAM,
- stabile Sortierung,
- Pagination/Cursor,
- Filter nach Kategorie, Endung, Größe, Pfadwort, Warnung und Duplikatgruppe,
- Suchvorlagen für häufige Chaos-Sammlungen,
- messbare Query-Dauer und Trefferzahl.

### GUI-004 – Duplicate Decision Model

- Duplikatgruppe als eigene View,
- Originalkandidat nur als Vorschlag,
- Hash, Größe, Datum und Pfad als Evidenz,
- niemals automatische Löschung,
- Papierkorb-/Undo-Plan zunächst nur simulieren.

### GUI-005 – Rename Preview Engine

- deterministische Namensbausteine,
- Kollisionsprüfung,
- Zeichen-/Pfadlängenprüfung,
- Vorher/Nachher-Liste,
- Rückübersetzbare Regeldefinition,
- Testlabor-Gate vor Freigabefähigkeit.
