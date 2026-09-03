# Architektur

## Zielbild

```text
┌──────────────── Benutzeroberfläche ────────────────┐
│ Dashboard · Hilfe · Status · Tooltips              │
└──────────────────────┬─────────────────────────────┘
                       ↓
┌──────────────── HTTP/API ──────────────────────────┐
│ Health · Aktionen · validierte Requests            │
└──────────────────────┬─────────────────────────────┘
                       ↓
┌──────────────── Anwendung ─────────────────────────┐
│ Fachlogik · Workflows · Validierungsverträge       │
└──────────────┬────────────────────┬────────────────┘
               ↓                    ↓
       Persistenz/Recovery     Logging/Diagnose
```

## Abhängigkeitsregel

UI darf keine Datenintegritätsregeln erfinden. Fachlogik darf keine UI-Farben kennen. Logging darf keine fachlichen Daten mutieren.

## Datenklassen

1. **Projektbasis** – versioniert.
2. **Standardkonfiguration** – versioniert, ohne private Werte.
3. **Nutzerdaten** – lokal, nicht versioniert.
4. **Laufzeitdaten** – lokal, rotierend, nicht versioniert.
5. **Backups** – lokal, nicht versioniert.
