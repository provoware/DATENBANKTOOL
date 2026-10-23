# PROVOWARE Release-Fortschrittsstandard (Pilot)

Dieser Standard ergänzt bestehende AGENTS.md-, Sicherheits-, Backup- und Restore-Regeln; strengere Schutzregeln bleiben maßgeblich. Einführung zunächst beobachtend, ohne zusätzliche blockierende Prüfungen.

Vor jeder Änderung: Release-Ziel und nachprüfbare Abschlussbedingung nennen, aktuellen Stand prüfen, tatsächlichen Nutzen und Risiko des Nichtstuns bewerten, Risiken der Änderung prüfen, vorhandene Belege wiederverwenden und verwandte Aufgaben auf gemeinsame Prüfungen untersuchen. Kritische Arbeiten nicht durch Bündelung verzögern.

Die kleinste geeignete Änderung mit angemessenem Budget durchführen. Schutzprüfungen nie aus Budgetgründen auslassen. Nach jeder Iteration erwartete und tatsächliche Wirkung, Prüfergebnisse, verbleibende Blocker und nächsten Release-Schritt dokumentieren. Wiederholte Analyse ohne neue Erkenntnis ist kein Fortschritt.

Bei unerwarteten Konflikten, widersprüchlichen Anforderungen oder möglichen irreversiblen Folgen die betroffene Änderung sicher anhalten, Optionen und Folgen verständlich erläutern und dem Nutzer eine konkrete Frage stellen. Unabhängige sichere Arbeit fortsetzen.

Eine automatische Pflichtprüfung erst nach erfolgreichem Pilot und nachgewiesenem Nutzen aktivieren.

## Verbindliche Zweistufigkeit und Freigabegrenze
**Stufe eins – Dokumentation und Planung:** Ist-Zustand, Ziele, Risiken, Abhängigkeiten, Alternativen, betroffene Dateien und erwartete Prüfnachweise festhalten. Keine Produktcodeänderung und keine automatische Freigabe durch bloße Planung. Laufende eingefrorene Pläne nicht still ändern.

**Stufe zwei – Umsetzung und Projektvalidierung:** Erst nach der nach den vorhandenen Projektregeln erforderlichen Planfreigabe und Prüfung von Ausgangsstand, Zuständigkeit, Schreibsperre und Änderungsumfang Produktcode ändern. Danach Tests, Regression, Sicherheits- und Release-Prüfungen am tatsächlichen Commit durchführen. Ein dokumentierter Plan ist niemals ein Implementierungs- oder Testnachweis.

Bei fehlender Freigabe oder widersprüchlichen Voraussetzungen bei Stufe eins bleiben und eine gezielte Nutzerfrage stellen. Keine Umgehung bestehender Schutzschranken, kein zweiter Schreiber für denselben Bereich und kein automatisches Zusammenführen offener Pull Requests.
