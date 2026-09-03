# FORTSCHRITTSINFO

## Aktueller Stand

**Version:** `0.2.0-alpha.1`  
**Status:** 🟡 `DATENKERN / AUFBAU`  
**Fortschritt:** `[■■■■□□□□□□] 40 %`

| Bereich | Status | Kurzdetail |
|---|---|---|
| Repository-Basis | 🟢 | Clean Foundation steht |
| Architekturtrennung | 🟢 | Basis/Config/Data/Runtime getrennt |
| Dokumentation | 🟢 | Kernunterlagen angelegt |
| CI / Tests | 🟢 | Basis-Gates aktiv |
| Logging | 🟢 | JSONL + TXT-Basis vorhanden |
| Persistenz | 🟢 | SQLite-Schema v1 + Migrationen + Integritätsprüfung |
| Recovery | 🟡 | formaler Transaktionsvertrag ist nächster P0-Schritt |
| Backup / Restore | 🟡 | nach Transaktionsvertrag |
| Fachmodule | 🟡 | bauen später auf gemeinsamem Datenkern auf |
| reale UI-Abnahme | 🔴 | noch nicht durchgeführt |

## Neu in diesem Stand

- Datenbank wird beim Start sicher initialisiert.
- Migrationen sind versioniert und per SHA-256 gegen unbemerkte Änderung geschützt.
- Schema enthält hierarchische Einträge, Tags und App-Einstellungen.
- `/api/health` meldet den Schema-Status.
- `/api/storage/status` liefert Schema- und Integritätsstatus.
- Automatische Tests prüfen Migration, Idempotenz, Fremdschlüssel und Integrität.

## Nächster sinnvoller Schritt

**P0-010 – Recovery-/Transaktionsvertrag für alle Datenänderungen.**

Ziel: `PRE → Mutation → POST → Commit` mit Fehlercode, Evidence und definierter
Rollback-Regel. Erst danach werden schreibende Hochrisiko-Aktionen freigegeben.

## Release-Regel

`STABLE` erst nach grünem Persistenz-, Recovery-, UI-, A11y- und Regression-Gate.
