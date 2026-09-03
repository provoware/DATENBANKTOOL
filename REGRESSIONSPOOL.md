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
