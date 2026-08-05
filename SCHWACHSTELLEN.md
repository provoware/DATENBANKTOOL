# Schwachstellen und Grenzen

Stand: Version `0.21.0-alpha.1`

## Behobene Schwachstellen

1. **Geführter Restore konnte kein optionales Protokollziel erfassen:** Nach exakter Sicherungsnamensbestätigung wird nun optional ein ausdrücklich eingegebener neuer Pfad aufgenommen.
2. **Leere Eingabe hätte unbeabsichtigt einen Pfad erzeugen können:** Leer bedeutet eindeutig kein Protokoll; der bisherige Befehl bleibt unverändert.
3. **Vorhandenes Protokollziel könnte überschrieben werden:** Existierende Ziele und Symlinks werden im Assistenten vor der Befehlsfreigabe abgelehnt.
4. **Automatische Zielwahl könnte falsche Dateien erzeugen:** Es gibt keinen Vorschlag, keine Suche, keine automatische Benennung oder Speicherung.
5. **Protokollprüfung war nur technisch per CLI erreichbar:** Die Startseite bietet nun eine eigene rein lesende Aktion an.
6. **Geführte Prüfung könnte unnötig eine Indexdatei verlangen:** `Protokoll prüfen` benötigt ausschließlich den ausdrücklich gewählten Protokollpfad.
7. **Falsche Protokolldatei könnte trotz gültigem Schema gewählt werden:** Optional kann exakt ihr erwarteter SHA-256-Wert verlangt werden.
8. **Pinprüfung nach der Schemaauswertung wäre zu spät:** Die Identität wird vor jedem JSON-Decoding und vor dem Schema-Prüfer bestätigt.
9. **Pin könnte unbemerkt automatisch ermittelt werden:** Nur der ausdrücklich eingegebene Wert wird verwendet; es gibt keine automatische Berechnung oder Historie.
10. **Groß-/Kleinschreibung oder verkürzte Hashes wären uneindeutig:** Akzeptiert werden ausschließlich 64 kleingeschriebene Hexzeichen.
11. **Große Startseitenklasse würde weiter wachsen:** Die neuen Dialoge liegen in einer kleinen Erweiterungsschicht; bestehende Abläufe bleiben unverändert.

## Verbleibende Grenzen

1. **Reale Laienabnahme offen:** Automatisierte Tests ersetzen keine Beobachtung einer unerfahrenen Person auf Kubuntu.
2. **Pfade bleiben sensible Metadaten:** Restore-Protokolle enthalten keine Konfigurationsinhalte, aber drei lokale Dateipfade.
3. **Kein automatischer Protokollfund:** Der Nutzer muss den vollständigen Pfad kennen und ausdrücklich eingeben.
4. **Kein Prüfbericht als Datei:** Terminal und JSON stehen bereit; ein eigener neuer Berichtspfad ist noch nicht implementiert.
5. **Pin muss extern bekannt sein:** Das Tool ermittelt oder speichert ihn bewusst nicht automatisch.
6. **Zentraler Prozessrahmen schreibt internes Laufjournal:** Die Fachprüfung verändert keine Prüfobjekte; das allgemeine Absturzjournal bleibt aktiv.
7. **Hardwaregrenzen:** Defekter Datenträger, beschädigtes oder volles Dateisystem, Kerneldefekt und physischer Verlust bleiben außerhalb des Anwendungsschutzes.

## Schutzverträge

- Geführter Restore ergänzt `--restore-log` nur bei ausdrücklicher nicht leerer Eingabe.
- Protokollziele müssen absolut beziehungsweise mit `~` angegeben, neu und nicht symlinkbasiert sein.
- Geführte Prüfung zeigt den vollständigen normalisierten Pfad vor der Freigabe.
- Keine automatische Suche, Auswahl, Benennung, Rotation oder Löschung.
- SHA-Pin-Prüfung erfolgt mit sicherer Nur-Lese-Öffnung und vor der Schemaauswertung.
- Falscher oder ungültiger Pin beendet fail-closed mit Code `2`.
- Protokoll und referenzierte Dateien bleiben unverändert.
- Originaldatei-Schreibzugriffe bleiben technisch gesperrt.

## Praktische Folge

```bash
datenbanktool start

datenbanktool index backups verify-log /pfad/restore.json \
  --expected-protocol-sha256 64_kleingeschriebene_hexzeichen
```

Der Vertrag verhindert automatische Pfadwahl und falsche Protokollidentität, ersetzt jedoch keine externe Datenträgersicherung oder reale Zielsystemabnahme.
