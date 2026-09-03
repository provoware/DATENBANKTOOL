# P0-012 · Browser-Endabnahme unter Kubuntu/KDE + Google Chrome

## Ziel

Diese Prüfung trennt automatische Browser-Smokes von der echten visuellen Endabnahme.
Ein grüner CI-Chromium-Lauf ersetzt **nicht** die reale Prüfung unter Kubuntu/KDE + Google Chrome.

## Teil A · automatischer Browser-Smoke

Auf dem Zielrechner im Projektordner ausführen:

```bash
bash tools/run_browser_acceptance.sh
```

Der Test startet den lokalen Server selbst und prüft:

- `/api/project/meta` ist erreichbar und passt zur sichtbaren Version.
- `/api/health` wird in der Oberfläche verarbeitet.
- Fortschrittswert und Footer stammen aus den Runtime-Metadaten.
- alle sechs Basiskarten sind vorhanden.
- 1366×768, 1600×900 und 1920×1080 erzeugen keinen horizontalen Seitenüberlauf.
- JavaScript-Konsole und Page-Errors bleiben leer.
- Kurzhilfe ist per Tastatur erreichbar und übernimmt beim Öffnen den Fokus.
- Skip-Link führt zum Hauptinhalt.

**Gate:** Alle automatischen Tests müssen grün sein.

## Teil B · reale KDE-/Chrome-Abnahmematrix

Die folgenden Punkte werden in einem **sichtbaren normalen Chrome-Fenster** geprüft.
Keine Headless-Ausführung darf hier als Ersatz gelten.

| ID | Prüfung | Erwartung | Ergebnis |
|---|---|---|---|
| UI-001 | Start bei 1366×768 | keine abgeschnittene Hauptfunktion, kein horizontaler Seiten-Scroll | ⬜ |
| UI-002 | Start bei 1600×900 | klare Hierarchie, Karten und Status vollständig sichtbar | ⬜ |
| UI-003 | Start bei 1920×1080 | keine übergroßen Leerflächen oder gestreckten Bedienelemente | ⬜ |
| UI-004 | Chrome-Zoom 100 % | vollständig bedienbar | ⬜ |
| UI-005 | Chrome-Zoom 125 % | Texte und Bedienelemente bleiben lesbar und erreichbar | ⬜ |
| UI-006 | Chrome-Zoom 150 % | keine Funktionsverluste, interne Umbrüche nachvollziehbar | ⬜ |
| UI-007 | Chrome-Zoom 200 % | Kernbedienung bleibt möglich, kein verdeckter Fokus | ⬜ |
| A11Y-001 | Tab-Reihenfolge | sichtbar, logisch, keine Fokusfalle | ⬜ |
| A11Y-002 | Skip-Link | springt sichtbar zum Hauptinhalt | ⬜ |
| A11Y-003 | Hilfe per Tastatur | Enter öffnet Hilfe, Fokus landet in Hilfe | ⬜ |
| VIS-001 | Ampeln | Farbe + Text/Symbol vermitteln denselben Zustand | ⬜ |
| VIS-002 | Kontrast | Texte, Buttons und Status auf dunklem Hintergrund eindeutig erkennbar | ⬜ |
| VIS-003 | Abstände | gleichartige Karten/Elemente wirken konsistent | ⬜ |
| ERR-001 | Server nicht erreichbar | rote verständliche Meldung statt leerer oder technischer Fehlerseite | ⬜ |
| ERR-002 | Recovery blockiert | Ursache und nächster Handlungsschritt sind verständlich | ⬜ |
| META-001 | Version/Status | sichtbare Metadaten stimmen mit `/api/project/meta` überein | ⬜ |
| OFF-001 | offline nach lokalem Start | Oberfläche lädt ohne externe Pflichtressourcen | ⬜ |
| KDE-001 | KDE Fenster maximiert | Layout reagiert ohne abgeschnittene Inhalte | ⬜ |
| KDE-002 | KDE Fenster verkleinert | Umbruch bleibt stabil, Fokus bleibt sichtbar | ⬜ |

## Evidence

Für jede rote Abweichung notieren:

1. Matrix-ID,
2. Bildschirmauflösung,
3. Chrome-Version,
4. Zoomstufe,
5. Schritte zur Reproduktion,
6. erwartetes Ergebnis,
7. tatsächliches Ergebnis,
8. Screenshot,
9. relevante Browser-Konsole, falls vorhanden.

Keine kosmetische Änderung wird ohne reproduzierbaren Befund in den P0-012-Patch aufgenommen.

## Abschlussregel

P0-012 darf erst abgehakt werden, wenn:

- automatischer Browser-Smoke grün ist,
- alle Matrixpunkte auf dem realen Kubuntu/KDE-/Chrome-Zielsystem geprüft sind,
- rote Befunde behoben und erneut geprüft wurden,
- abschließende Repository-CI und Release Gate auf demselben finalen Head grün sind.
