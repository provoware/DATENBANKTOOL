# TODO · CLEAN FOUNDATION

**Status:** 🟡 TRANSAKTIONSKERN / AUFBAU  
**Fortschritt:** `[■■■■■□□□□□] 50 %`

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
- [ ] **P0-011** Backup-/Restore-Funktion mit Integritätsprüfung implementieren.
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
