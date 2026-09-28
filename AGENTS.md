## Projekt-Konfiguration
- **Git-Workflow:** vereinfacht
- **Doku-Sprache:** Deutsch
- **GitHub:** https://github.com/simongoldenberg/event-curator-app

## Projekt
Lokale Python-CLI zur regionalen Eventsuche, zum Präferenzinterview und zur Erstellung persönlicher Monatsberichte.

## Architektur-Constraints
- Python 3.11 oder neuer; nur Standardbibliothek, kein Build-Schritt und keine Weboberfläche.
- Daten, Profile, Zugangsdaten, Exporte und Laufstatus bleiben lokal. Keine persönlichen Daten in Git.
- Live-Abfragen sind explizit; der Beispielmodus arbeitet offline mit fiktiven Events.
- Quellenadapter liefern ein gemeinsames Eventmodell. Region und Datum werden anschließend zentral geprüft.
- Keine automatischen Browser-/UI-Tests erforderlich (CLI-Projekt).

## Dateistruktur
- `main.py`: CLI-Einstieg; `config.py`: öffentliche Standardwerte und lokale Konfiguration.
- `event_curator/`: Datenmodelle, Interview, Matching, Reports und Quellenadapter.
- `event_curator/discovery.py`: belegbasierte Artist-/Venue-Vorschläge und unbestätigte Gig-Hinweise.
- `data/sample_artists.csv`: ausschließlich fiktive öffentliche Beispieldaten.
- `scripts/`: GitHub-Setup, Datenschutzprüfung und monatliche Ausführung.
- `tests/`: Offline-Tests mit synthetischen Daten.
- `data/user_*`, `.env`, `exports/`: lokale, ignorierte Nutzerdaten.

## Versionierung
`event_curator/__init__.py` enthält `APP_VERSION`; CLI und Reports zeigen sie an.
Neue Versionen erst für stabile Releases; README und CHANGELOG dabei synchron halten.

## Entwicklung und neue Funktionen
Direkt auf `develop` arbeiten; `main` enthält stabile Releases. PRs und Releases nur nach Bestätigung.
Neue Quellen in `event_curator/sources/` ergänzen, CLI-Optionen in `event_curator/cli.py`.
Gemeinsame Filter bleiben im Matching-Modul. Keine persönlichen Fixtures oder Keys in Tests.
Vor Upload Datenschutzprüfung und Offline-Tests ausführen. Dokumentation auf Deutsch pflegen.
Recherchehinweise aus Clubs, Festivals und SoundCloud nicht ohne Datum-/Ortsprüfung in Events umdeuten.
Artist-Vorschläge nicht automatisch zu Favoriten machen. Die Recherche darf überregional sein,
der Monatsdigest muss den Regionsfilter behalten. Unbekannte Venue-Domains lokal konfigurieren.
