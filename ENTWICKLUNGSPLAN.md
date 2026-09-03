# ENTWICKLUNGSPLAN

## Phase A · Clean Foundation – 🟢

Ziel: sauberer, verständlicher, prüfbarer Unterbau.

- Repository neu strukturieren
- Standards festlegen
- Dokumentation anlegen
- CI / Formatierung / Tests etablieren
- Logging-Basis schaffen

## Phase B · Datenkern – 🟡

Ziel: robuste Datenhaltung ohne Datenverlust.

1. ✅ Schema v1 definieren
2. ✅ versionierte Migrationen und Drift-Erkennung
3. ✅ zentraler Transaktions- und Validierungsvertrag
4. ✅ Recovery-Journal + Operation-ID + Start-Gate
5. 🔄 Backup / Restore mit Integritätsprüfung
6. ⬜ Import / Export mit Schema-Vertrag

## Phase C · Hauptdatenbank – ⚪

Ziel: Fachmodule auf gemeinsamem Datenkern.

- Dashboard
- Wissens-/Archivmodule
- globale Suche
- Querverweise / Tags / Favoriten
- Profile / Presets

## Phase D · Bedienhärtung – ⚪

- Tastaturbedienung
- Zoom 100–200 %
- Screenreader-Texte
- klare Fehler-/Leermeldungen
- 1–2-Klick-Workflows

## Phase E · Release – ⚪

- Realtest Kubuntu/KDE + Chrome
- Windows-Pfadtest
- große Datenbestände
- Recovery-/Crash-Testmatrix
- Manifest-/Fresh-Extract-Prüfung
- STABLE-Gate
