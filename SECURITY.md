# Sicherheit

## Nicht ins Repository

- Passwörter
- API-Keys / Tokens
- Cookies
- echte Account-/E-Mail-Daten
- Browserprofile
- private Konfiguration
- Nutzerdatenbanken
- Laufzeitlogs
- Backups

## Fehlerberichte

Vor dem Teilen prüfen, ob Logs sensible Inhalte enthalten. Die Logging-Basis schwärzt bekannte sensible Schlüsselnamen automatisch; dies ersetzt keine bewusste Datenminimierung.

## Lokaler Betrieb

Der Basisserver bindet standardmäßig ausschließlich an `127.0.0.1`.
