# Entwicklerdokumentation

## Architekturstand `0.21.0-alpha.1` / `0.21.0a1`

Diese Iteration ergänzt drei zusammenhängende, aber technisch getrennte Verträge:

1. optionale Erfassung eines neuen Restore-Protokollpfads in der geführten Startseite,
2. geführte rein lesende Prüfung genau eines Restore-Protokolls,
3. optionaler SHA-256-Pin der Protokolldatei vor jeder JSON-Schemaauswertung.

Originaldatei-Schreibzugriffe bleiben gesperrt. Es gibt keine Shell-Auswertung, automatische Protokollsuche, Zielwahl, Pin-Ermittlung, Historie, Rotation oder Löschung.

## Fachmodule

| Modul | Verantwortung |
|---|---|
| `core/terminal_home.py` | bestehende Recovery-, Sicherungs- und Restore-Basis |
| `core/terminal_home_restore_audit.py` | kleine Erweiterung für optionalen Restore-Protokollpfad und geführte Protokollprüfung |
| `entrypoint.py` | aktiviert die erweiterte Startseitenklasse |
| `core/restore_audit.py` | bestehende Protokollerzeugung, Schema- und Drei-Dateien-Prüfung |
| `core/restore_audit_identity.py` | Pinformat und sichere Protokollidentitätsprüfung vor Schemaauswertung |
| `cli_restore_audit.py` | Parser, Prüfungsreihenfolge sowie Terminal-/JSON-Darstellung |
| `tests/test_guided_restore_audit.py` | geführte Pfad-, Nichtüberschreibungs- und Argumentlistenverträge |
| `tests/test_restore_audit_identity.py` | Pin-, Reihenfolge- und Unverändertheitstests |

## Geführter Restore-Protokollpfad

Die Basisklasse erstellt nach Vergleich, exakter Namenswiederholung und `--yes` weiterhin dieselbe sichere Restore-Argumentliste. Die Erweiterungsklasse prüft anschließend ausschließlich, ob die Liste mit

```text
index backups restore
```

beginnt. Nur dann wird optional gefragt:

```text
Optionaler neuer Protokollpfad; leer bedeutet kein Protokoll
```

### Vertrag

1. Leere Eingabe liefert die bestehende Argumentliste unverändert zurück.
2. Nicht leere Eingabe muss absolut oder über `~` angegeben werden.
3. Der Pfad wird lexikalisch normalisiert und vollständig angezeigt.
4. Ein vorhandenes Ziel wird abgelehnt.
5. Ein Symlink-Ziel wird abgelehnt.
6. Nur ein akzeptierter Pfad ergänzt `--restore-log PFAD`.
7. Danach bleibt die vollständige Befehlsbestätigung der Startseite erforderlich.
8. Es gibt keinen Standardpfad und keine automatische Verzeichnis- oder Dateinamenswahl.

Die eigentliche Restore- und Protokollschreiblogik bleibt unverändert in `cli_backups.py`, `core/config_restore.py` und `core/restore_audit.py`.

## Geführte Protokollprüfung

Die neue Aktion ist unter „Sicherungen verwalten“ über `Protokoll prüfen`, `prüfen`, `p` oder `verify-log` erreichbar.

### Ablauf

1. Genau einen vollständigen Protokollpfad eingeben.
2. Absolute Form oder `~` verlangen.
3. Normalisierten vollständigen Pfad anzeigen.
4. Optional einen erwarteten SHA-256-Pin eingeben.
5. Leere Pin-Eingabe überspringt den Pin vollständig.
6. Nicht leerer Pin wird vorab auf exakt 64 kleingeschriebene Hexzeichen geprüft.
7. Sichere Argumentliste erzeugen:

```text
index backups verify-log PROTOKOLL
```

oder

```text
index backups verify-log PROTOKOLL
  --expected-protocol-sha256 SHA256
```

8. Der vorhandene Startseitenvertrag zeigt den vollständigen Befehl und verlangt die finale Bestätigung.
9. Die CLI liefert danach dieselbe Grün-/Gelb-/Rot-Auswertung wie bei direktem Terminalaufruf.

Die geführte Prüfung fragt bewusst nicht nach einer Indexdatei und durchsucht keine Ordner.

## Optionaler Protokoll-SHA-Pin

Öffentlicher Befehl:

```text
index backups verify-log PROTOKOLL
  [--expected-protocol-sha256 SHA256]
  [--json]
```

### Reihenfolge

`run_restore_audit_verification()` führt strikt aus:

1. Nur wenn die Option gesetzt ist: `verify_restore_audit_identity()`.
2. Erst nach erfolgreicher Identitätsbestätigung: `verify_restore_audit_log()`.
3. Danach Terminal- oder JSON-Ausgabe.

Tests patchen den Schema-Prüfer und bestätigen, dass er bei falschem oder ungültigem Pin nicht aufgerufen wird.

### Sichere Identitätsprüfung

`verify_restore_audit_identity()` verlangt:

- exakt 64 kleingeschriebene Hexzeichen,
- ausdrücklich ausgewählten Pfad,
- kein Symlink-Protokoll,
- normale Datei über `fstat()`,
- Öffnung mit `O_RDONLY`, `O_CLOEXEC` und – sofern verfügbar – `O_NOFOLLOW`,
- Streaming-SHA-256 in 1-MiB-Blöcken.

Bei Abweichung wird `ValueError` ausgelöst. Die allgemeine CLI-Grenze übersetzt dies in Rückgabecode `2`. JSON-Schema und referenzierte Dateien werden nicht geprüft.

### Ausgabe

Bei erfolgreichem Pin zeigt das Terminal erwarteten und tatsächlichen Protokoll-SHA-256-Wert. JSON ergänzt:

```json
{
  "protocol_identity": {
    "protocol": "/absoluter/pfad/restore.json",
    "expected_sha256": "...",
    "actual_sha256": "...",
    "matches": true
  }
}
```

Ohne Option bleibt die bisherige Ausgabe kompatibel und enthält kein `protocol_identity`-Feld.

## Architekturgrenzen

- Die bestehende umfangreiche Startseitenklasse wird nicht weiter vergrößert.
- Erweiterung erfolgt per kleiner Unterklasse und überschreibt nur `_backup_action()` und `_build_backup()` sowie neue Hilfsmethoden.
- `entrypoint.py` tauscht ausschließlich den importierten Startseitentyp aus.
- `cli_restore_audit.py` bleibt deutlich unter 500 Zeilen.
- Keine zyklischen CLI-Importe.
- Kein `subprocess`, `shell=True`, `os.system`, `eval` oder `exec`.
- Keine neue Laufzeitabhängigkeit.
- Keine Änderung der Originaldatei-Sperre.

## Automatische Prüfungen

Die Version enthält 158 Tests, darunter:

- expliziter neuer Restore-Protokollpfad wird korrekt angehängt,
- leere Eingabe lässt die Argumentliste unverändert,
- vorhandenes Ziel wird nicht überschrieben oder angehängt,
- geführte Prüfung benötigt keine Datenbank,
- vollständiger Pfad wird sichtbar ausgegeben,
- Pin kann gesetzt oder übersprungen werden,
- richtiger Pin erscheint in JSON und bestätigt die Datei,
- falscher Pin stoppt vor Schemaauswertung,
- ungültiges Pinformat stoppt vor Schemaauswertung,
- Protokoll und Referenzdateien bleiben unverändert,
- bestehende Restore-, Rückfall-, Protokoll-, Recovery- und Architekturtests bleiben grün,
- Versionsdrift wird geprüft.

Die Matrix läuft unter Python 3.10 und 3.12 mit `PYTHONWARNINGS=error`. Quick- und Standardabnahme verwenden ausschließlich synthetische Daten und bestehen jeweils 11/11 Kriterien.

## Verbleibende Grenzen

- Reale Laienabnahme auf Kubuntu ist offen.
- Nutzer müssen Protokollpfad und optionalen Pin selbst kennen.
- Ein eigener Prüfberichtsexport ist noch nicht implementiert.
- Das zentrale Laufjournal des Prozessrahmens bleibt bei Fachbefehlen aktiv, verändert aber keine Prüfobjekte.
- Hardware-, Kernel-, Dateisystem- und physischer Verlust bleiben außerhalb des Anwendungsschutzes.

## Releaseprüfung

```bash
python -m json.tool registry.json >/dev/null
python -m json.tool project_registry.json >/dev/null
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
python -m datenbanktool --version
python -m datenbanktool index backups verify-log --help
python -m datenbanktool check
```

`AGENTS.md` und die Sperre automatischer Originaldateioperationen bleiben unverändert.
