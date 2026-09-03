# TODO · CLEAN FOUNDATION

**Status:** 🟡 RESTOREKERN / AUFBAU  
**Fortschritt:** `[■■■■■■■□□□] 70 %`

## P0 · Muss vor erster produktiver Nutzung

- [x] **CF-001** Sicherheits-Branch des Altbestands anlegen.
- [x] **CF-002** Repository auf Clean Foundation zurücksetzen.
- [x] **CF-003** Nutzerdaten, Logs und lokale Konfiguration vom Basistool trennen.
- [x] **CF-004** README, CHANGELOG, TODO, REGRESSIONSPOOL, FORTSCHRITTSINFO,
  ENTWICKLUNGSPLAN und AGENTS anlegen.
- [x] **CF-005** Manifest mit Datei-/Zeilengrenzen und Qualitätsstandards anlegen.
- [x] **CF-006** CI, Formatierung, Tests und Projektprüfer anlegen.
- [x] **CF-007** professionelles JSONL-/TXT-Logging als Basis implementieren.
- [x] **CF-008** deutsche Laienhilfe, Tooltips-Regeln, Ampeln und Fortschrittsdarstellung anlegen.
- [x] **P0-009** Persistenzschicht mit echtem Schema und Migration implementieren.
- [x] **P0-010** Recovery-/Transaktionsvertrag für alle Datenänderungen implementieren.
  - [x] Operation-ID pro Datenänderung.
  - [x] Zustandsmaschine PRECHECK → MUTATION → POSTCHECK → COMMIT/ROLLBACK → EVIDENCE.
  - [x] zentraler Single-Writer-Gate gegen parallele kritische Mutationen.
  - [x] Idempotenzschlüssel gegen Doppel-Submit / Doppelklick.
  - [x] maschinenlesbares JSONL-Recovery-Journal.
  - [x] atomare finale Evidence-Datei mit Status im Dateinamen.
  - [x] sensible Evidence-Details werden geschwärzt.
  - [x] Start-Gate erkennt unvollständige vorherige Operationen.
- [x] **P0-011** Backup-/Restore-Funktion mit Integritätsprüfung implementieren.
  - [x] **P0-011A** Backup Engine + Backup Manifest v1.
    - [x] konsistenter SQLite-Snapshot auch bei WAL-Betrieb.
    - [x] eindeutige Backup-ID.
    - [x] SHA-256 und Dateigröße.
    - [x] Schema-Version und UTC-Zeit.
    - [x] Manifest-Version und Integritätsstatus.
    - [x] atomare Veröffentlichung erst nach erfolgreicher Verifikation.
    - [x] `.incomplete_*` wird niemals als gültiges Backup geführt.
    - [x] unabhängiges Backup-Verifikations-Gate.
    - [x] Regressionen für WAL, Manipulation, Staging und Abbruch.
  - [x] **P0-011B** Staging-Restore implementieren.
    - [x] Backup vor Restore erneut verifizieren.
    - [x] Restore ausschließlich in Staging-Ziel durchführen.
    - [x] SHA-256, Schema, quick_check und foreign_key_check erneut prüfen.
    - [x] exklusives Datenbankzugriffsfenster vor dem Swap.
    - [x] Rollback-Snapshot des vorherigen Produktivstands vor dem Austausch.
    - [x] produktive Datenbank erst nach grünem Staging-Gate atomar austauschen.
    - [x] Fehler vor Austausch verändern keine produktiven Nutzdaten.
    - [x] POSTCHECK nach Swap ist Pflicht vor COMMITTED.
    - [x] fehlgeschlagener POSTCHECK rollt auf den vorherigen Produktivstand zurück.
    - [x] Crash im Zustand SWAPPING bleibt als unvollständiger Vorgang startblockierend sichtbar.
    - [x] Restore-Evidence und Recovery-Vertrag angebunden.
- [ ] **P0-012** reale Browser-Endabnahme unter Kubuntu/KDE + Chrome durchführen.

## P1 · Produktbasis

- [ ] **P1-001** Dashboardmodule aus fachlichen Anforderungen ableiten und priorisieren.
- [ ] **P1-002** globale Suche und Filterarchitektur implementieren.
- [ ] **P1-003** barrierefreie Tastaturnavigation und Fokusführung vollständig prüfen.
- [ ] **P1-004** Zoomtests 100 / 125 / 150 / 200 % durchführen.
- [ ] **P1-005** Import-/Exportvertrag mit Schema-Versionierung implementieren.
- [ ] **P1-006** Plugin-/Erweiterungsschnittstelle definieren.

## P2 · Qualität & Komfort

- [ ] **P2-001** Recovery-Center visualisieren.
- [ ] **P2-002** Fehlercodes mit kontextbezogenen Lösungstipps erweitern.
- [ ] **P2-003** automatische Updateprüfung optional entwerfen.
- [ ] **P2-004** Performance-Gate mit großem Testdatenbestand hinzufügen.
- [ ] **P2-005** Windows-Pfadtest und Launcher ergänzen.

## Regel

Neue TODOs erhalten eine stabile ID und werden nicht gelöscht.
Erledigte Punkte werden abgehakt und im `CHANGELOG.md` erwähnt.
