# Premium V2 Iteration 013 – Strukturvergleich mit DATENBANKTOOL/main

## Sicherheitsrahmen

- Basis: `provoware/DATENBANKTOOL:main`
- Integrationsbranch: `agent/premium-v2-iter013-integration`
- `main` bleibt unverändert.
- Ziel ist eine selektive Integration kompatibler Backend-Verträge, kein mechanisches Überschreiben der bestehenden 0.21-Produktlinie.

## Produktidentität

| Bereich | DATENBANKTOOL/main | Premium V2 Iteration 013 |
|---|---|---|
| Distribution | `datenbanktool` | `datanavigator-premium-v2` |
| Version | `0.21.0a1` | `0.1.0` |
| Namespace | `datenbanktool` | `datanavigator` |
| CLI | `datenbanktool.entrypoint:main` | `datanavigator.app.main:main` |
| Python | `>=3.10` | `>=3.10` |
| Laufzeitabhängigkeiten | 0 | 0 |
| Persistenz | eigene 0.21-Schemahistorie | Premium V2 Schema V1–V4 |

## Wesentliche Strukturunterschiede

### DATENBANKTOOL/main

Die 0.21-Linie besitzt bereits eine breite Nutzer- und Betriebsoberfläche: geführte Startseite, viele CLI-Subcommands, Restore/Backup/Recovery, Berichte, Suche, Timeline, RunJournal und Crashgrenzen.

Der aktuelle Index-Build führt Metadatenscan, eine optionale Hashphase und die Duplicate-Gruppenbildung innerhalb derselben Build-Zustandsmaschine aus. SHA-256 wird dabei über den relativen Dateipfad geöffnet.

### Premium V2 Iteration 013

Premium V2 trennt die Verantwortungen:

```text
VolumeRegistry
  -> FileSystemScanner (nur Metadaten)
  -> FileCatalogRepository (Current State + immutable Revisionen)
  -> SecureHashPipeline (explizit an revision_id gebunden)
  -> file_hashes
  -> DuplicateRevisionAnalyzer (nur SELECT)
```

Zusätzliche Premium-Verträge:

- stabile `volume_uuid` mit Online/Offline/Reattached,
- atomarer Scan-Batch-/Checkpoint-Commit,
- persistenter Scan-Run-State,
- Digest-verifizierter Resume,
- konservatives `present -> missing -> deleted`,
- no-follow Hashöffnung über Directory-FDs,
- Pre-/Post-Stat-Driftprüfung,
- Hardlink-/Content-Duplicate-Trennung.

## Direkte Merge-Konflikte

1. **Namespace/Entry Point:** unterschiedliche Paketnamen und Importpfade.
2. **Datenmodell:** unterschiedliche SQLite-Migrationen und Tabellenverträge; gleiche Versionsnummern wären nicht semantisch gleich.
3. **Hashing:** DATENBANKTOOL koppelt Hashing an den Index-Build; Premium V2 behandelt Hashing als separaten revisionsgebundenen Service.
4. **Duplicate-Semantik:** Premium V2 trennt reine Hardlinks von zusätzlichen physischen Inhaltskopien.
5. **Resume:** beide Linien besitzen Wiederanlaufmechanismen, aber Premium bindet Checkpoints zusätzlich an Volume, Root, Scannervertrag und Traversal-Digest.

## Empfohlene Integrationsreihenfolge

1. `main` unverändert lassen.
2. Schema- und Begriffs-Mapping dokumentieren.
3. Premium-Hash-Safety als isolierten Backend-Vertrag bewerten.
4. Hardlink-vs.-Content-Duplicate-Semantik übernehmen.
5. Premium-Checkpoint-Invarianten gegen die bestehende 0.21-Resume-Logik testen.
6. Erst danach über eine gemeinsame Persistenzschicht entscheiden.
7. Bestehende CLI-, Restore-, Report- und Laienführung von DATENBANKTOOL erhalten.

## Ergebnis

Die Linien sind funktional verwandt, aber nicht merge-identisch. Der professionelle Integrationsweg ist die gezielte Übernahme stärkerer Premium-V2-Backend-Invarianten in die reifere DATENBANKTOOL-Produktoberfläche, nicht eine Komplettüberschreibung.