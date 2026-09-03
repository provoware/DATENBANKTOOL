# REGRESSIONSPOOL

Wiederkehrende Prüfungen, die bei relevanten Änderungen erneut laufen müssen.

## Start & Betrieb

- [ ] **REG-START-001** Tool startet ohne Traceback.
- [ ] **REG-START-002** `/api/health` liefert HTTP 200 und `ok=true`.
- [ ] **REG-START-003** Portkollision erzeugt verständliche Fehlermeldung.
- [ ] **REG-START-004** Fehlender Schreibzugriff verursacht keine stille Datenbeschädigung.

## Architektur & Wartbarkeit

- [x] **REG-ARCH-001** Produktversion ist in `VERSION.json`, Manifest und UI-Metadaten identisch.
- [x] **REG-ARCH-002** Registry-IDs und API-Kombinationen sind eindeutig; registrierte Modulpfade existieren.
- [x] **REG-ARCH-003** Recovery-, Backup- und Restore-Vertragsversionen stimmen mit dem Manifest überein.
- [x] **REG-ARCH-004** deutscher Sprachkatalog ist versioniert und enthält die erforderlichen UI-Texte.
- [x] **REG-ARCH-005** UI verwendet zentrale Tokens für Abstände, Radien, Schatten und semantische Farben.
- [x] **REG-ARCH-006** alle kritischen Pfade aus `TOOL_SCHEMA.json` existieren.

## Daten

- [ ] **REG-DATA-001** keine echten Nutzerdaten im Repository.
- [ ] **REG-DATA-002** Import verändert Daten nur nach erfolgreicher Vorprüfung.
- [ ] **REG-DATA-003** Export ist vollständig und schema-versioniert.
- [ ] **REG-DATA-004** Recovery stellt letzten gültigen Zustand wieder her.
- [x] **REG-DATA-005** frische Datenbank migriert automatisch auf Schema v1.
- [x] **REG-DATA-006** wiederholte Initialisierung ist idempotent.
- [x] **REG-DATA-007** geänderte Migrations-Prüfsumme blockiert den Start.
- [x] **REG-DATA-008** ungültige Elternreferenzen werden durch Fremdschlüssel verhindert.
- [x] **REG-DATA-009** `quick_check` und Fremdschlüsselprüfung sind auf frischer DB grün.
- [x] **REG-DATA-010** fehlgeschlagener POSTCHECK rollt Business-Daten vollständig zurück.
- [x] **REG-DATA-011** parallele kritische Mutation wird am Single-Writer-Gate abgewiesen.
- [x] **REG-DATA-012** derselbe Idempotenzschlüssel kann nicht zweimal committen.
- [x] **REG-DATA-013** COMMITTED/ROLLED_BACK/REJECTED erzeugen maschinenlesbare Evidence.
- [x] **REG-DATA-014** sensible Evidence-Details werden geschwärzt.
- [x] **REG-DATA-015** unvollständige Journaloperationen werden beim Start als kritisch erkannt.
- [x] **REG-DATA-016** SQLite-Backup enthält committed Daten aus einer WAL-Quelldatenbank.
- [x] **REG-DATA-017** Backup-Manifest v1 stimmt mit Hash, Größe und Schema des Snapshots überein.
- [x] **REG-DATA-018** manipulierte Snapshot-Datei scheitert am Verifikations-Gate.
- [x] **REG-DATA-019** manipuliertes Backup-Manifest scheitert am Verifikations-Gate.
- [x] **REG-DATA-020** `.incomplete_*`-Backup wird niemals als gültige Sicherung akzeptiert.
- [x] **REG-DATA-021** Fehler vor atomarer Veröffentlichung hinterlässt kein gültiges Backup.
- [x] **REG-DATA-022** fehlgeschlagener Staging-Restore verändert niemals die Produktivdatenbank.
- [x] **REG-DATA-023** erfolgreicher Restore tauscht erst nach vollständigem Staging-Gate atomar aus.
- [x] **REG-DATA-024** Backup wird unmittelbar vor Restore erneut verifiziert.
- [x] **REG-DATA-025** Staging besteht SHA-256, Schema, `quick_check` und Fremdschlüsselprüfung.
- [x] **REG-DATA-026** kontrollierter Fehler nach `SWAPPED` stellt den vorherigen Produktivstand wieder her.
- [x] **REG-DATA-027** Restore wird erst nach grünem produktivem POSTCHECK als COMMITTED markiert.
- [x] **REG-DATA-028** Prozessabbruch an der Swap-Grenze bleibt als `SWAPPING` startblockierend sichtbar.
- [x] **REG-DATA-029** Swap-Evidence enthält Restore-Hash, vorherigen Hash und Rollback-Pfad.
- [x] **REG-DATA-030** Restore-Staging wird nach kontrollierter Ablehnung bereinigt.
- [x] **REG-DATA-031** Mutation und Restore teilen denselben exklusiven kritischen Datenbank-Gate.

## Logging

- [ ] **REG-LOG-001** Maschinenlog ist gültiges JSONL.
- [ ] **REG-LOG-002** sensible Schlüssel werden geschwärzt.
- [ ] **REG-LOG-003** Kurzbericht enthält Ampel, Fehlercode und Handlungstipp.
- [ ] **REG-LOG-004** Logrotation hält definierte Grenzen ein.

## UI / Bedienung

- [ ] **REG-UI-001** keine Pflichtfunktion ist nur über Maus erreichbar.
- [ ] **REG-UI-002** Fokus ist sichtbar.
- [ ] **REG-UI-003** Text bleibt bei 200 % Zoom nutzbar.
- [ ] **REG-UI-004** Rot/Gelb/Grün werden zusätzlich durch Text/Symbol erklärt.
- [ ] **REG-UI-005** Tooltips ersetzen keine zwingend sichtbaren Kerninformationen.

## Release-Gate

Ein Release darf nur als `STABLE` markiert werden, wenn alle P0-Regressionen
und alle im Manifest als `release_blocking` markierten Prüfungen grün sind.
