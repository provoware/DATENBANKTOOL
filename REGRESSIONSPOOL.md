# REGRESSIONSPOOL

Wiederkehrende Prüfungen, die bei relevanten Änderungen erneut laufen müssen.

## Start & Betrieb

- [ ] **REG-START-001** Tool startet ohne Traceback.
- [ ] **REG-START-002** `/api/health` liefert HTTP 200 und `ok=true`.
- [ ] **REG-START-003** Portkollision erzeugt verständliche Fehlermeldung.
- [ ] **REG-START-004** Fehlender Schreibzugriff verursacht keine stille Datenbeschädigung.

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
- [ ] **REG-DATA-022** Staging-Restore verändert bei fehlgeschlagener Prüfung niemals die Produktivdatenbank.
- [ ] **REG-DATA-023** erfolgreicher Restore tauscht erst nach vollständigem Staging-Gate atomar aus.

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
