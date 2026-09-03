# Laienhilfe

## Was ist das PROVOWARE DATENBANKTOOL?

Das Tool ist eine lokale Grundlage zum Speichern, Ordnen, Finden und sicheren Wiederherstellen von Informationen.
Es arbeitet **offline-first**: Nutzerdaten bleiben grundsätzlich auf dem eigenen Rechner.

Der aktuelle Stand ist noch eine Entwicklungsfassung. Der Datenkern, sichere Änderungen, Backups und Restore sind technisch abgesichert. Die reale Browser-Endabnahme steht noch aus.

## Wo liegen meine Daten?

- `data/user/` – Ihre lokale SQLite-Datenbank.
- `backups/` – lokale, verifizierte Sicherungen.
- `logs/` – verständliche Kurzberichte und technische Protokolle.
- `runtime/` – Recovery-Zustand für sichere Wiederaufnahme nach Fehlern.

Diese Ordner mit echten Laufzeitdaten gehören **nicht** in das Git-Repository.

## Was bedeuten Backup und Restore?

**Backup** bedeutet Sicherung. Das Tool erstellt dafür einen geprüften Datenbank-Snapshot und kontrolliert Hash, Größe, Schema und Datenbankintegrität.

**Restore** bedeutet Wiederherstellung. Eine Sicherung ersetzt niemals sofort die aktive Datenbank. Sie wird zuerst separat geprüft. Erst wenn alle Prüfungen grün sind, darf der atomare Austausch erfolgen.

## Was passiert bei einem Fehler?

1. Eine kritische Änderung erhält eine eindeutige Operation-ID.
2. Vor und nach der Änderung werden Sicherheitsprüfungen ausgeführt.
3. Bei kontrollierten Fehlern wird zurückgerollt, wenn das möglich und geprüft ist.
4. Bei einem Absturz bleibt Recovery-Evidence erhalten.
5. Ein unklarer vorheriger Zustand blockiert neue kritische Änderungen, statt still weiterzumachen.

## Ampeln

### 🟢 GRÜN

Prüfung bestanden. Dieser Bereich hat aktuell keinen bekannten Blocker.

### 🟡 GELB

Der Bereich ist nutzbar oder weiterentwickelbar, aber noch nicht vollständig releasefertig.

### 🔴 ROT

Eine notwendige Prüfung fehlt oder ein Fehler blockiert den nächsten sicheren Schritt.

### 🟣 INFO

Nur Erklärung oder Hinweis – kein Fehler.

## Wenn etwas nicht funktioniert

1. Terminal-/Konsolenfenster offen lassen.
2. Kurzbericht im Ordner `logs/` ansehen.
3. Auf **Fehlercode**, **Kurzursache**, **Operation-ID** und **Tipp** achten.
4. Dieselbe kritische Änderung nicht mehrfach anklicken, wenn Recovery einen unvollständigen Vorgang meldet.
5. Bei wiederholtem Fehler zusätzlich die passende `.jsonl`-Datei zur Analyse verwenden.

## Fachbegriffe in einfacher Sprache

- **API** – Verbindung zwischen Oberfläche und Programmlogik.
- **Atomarer Austausch** – die alte Datei wird in einem einzigen Dateisystem-Schritt durch die neue ersetzt.
- **Hash / SHA-256** – digitaler Fingerabdruck einer Datei.
- **JSONL** – technische Protokolldatei; ein Ereignis pro Zeile.
- **Recovery** – kontrollierte Wiederaufnahme oder Rekonstruktion nach Fehler oder Absturz.
- **Regression** – ein bereits behobener Fehler taucht wieder auf.
- **Registry** – zentrales Verzeichnis stabiler Module, Endpunkte und technischer IDs.
- **Schema** – festgelegter Aufbau gespeicherter Daten.
- **Staging** – separater Prüfbereich, bevor produktive Daten verändert werden.

## Wo finde ich die Projektstruktur?

`ORDNER_UND_DATEIINDEX.md` erklärt die wichtigsten Ordner und Dateien in normaler Sprache.
`TOOL_SCHEMA.json` enthält dieselbe Grundstruktur maschinenlesbar.
