## Projekt-Konfiguration
- **Git-Workflow:** vereinfacht
- **Doku-Sprache:** Deutsch
- **GitHub:** https://github.com/simongoldenberg/event-curator-app
- **Browsertests durch Codex:** ja
- **Skyseed-Design-Skill:** nein

## Projekt
Lokale Python-CLI zur regionalen Eventsuche, zum Präferenzinterview und zur Erstellung persönlicher Monatsberichte mit interaktiver HTML-Oberfläche.

## Architektur-Constraints
- Python 3.11 oder neuer; nur Standardbibliothek und kein Build-Schritt. Die HTML-Oberfläche wird lokal generiert und öffnet sich auch ohne Webserver.
- Daten, Profile, Zugangsdaten, Exporte und Laufstatus bleiben lokal. Keine persönlichen Daten in Git.
- Live-Abfragen sind explizit; der Beispielmodus arbeitet offline mit fiktiven Events.
- Quellenadapter liefern ein gemeinsames Eventmodell. Region, Reiseland und Datum werden anschließend zentral geprüft.
- Würzburg hat mindestens 100 km Suchradius, die anderen vier Städte standardmäßig 50 km; `config.radius_for_region` ist die gemeinsame Regel für Abfrage, Matching und Karte.
- UI-Änderungen im Browser prüfen; die Oberfläche darf keine externen Karten-/Tracking-Dienste nachladen.

## Dateistruktur
- `main.py`: CLI-Einstieg; `config.py`: öffentliche Standardwerte und lokale Konfiguration.
- `event_curator/`: Datenmodelle, Interview, Matching, Reports, lokaler Venue-Katalog und Quellenadapter.
- `event_curator/venue_catalog.py`: lädt `data/user_venues.json` mit privaten Artist-/Venue-Belegen für Berichte.
- `event_curator/source_catalog.py`: öffentlicher Katalog offizieller Club- und Festivalprogramme; unterscheidet direkte Eventadapter, lokale Seitenrecherche, Links und Archive.
- `event_curator/discovery.py`: belegbasierte Artist-/Venue-Vorschläge und unbestätigte Gig-Hinweise.
- `event_curator/spotify.py`: lokaler Spotify-Audioimport in eine ignorierte Artist-CSV; keine Rohdaten im Repository.
- `event_curator/sources/clubs.py`: direkte Adapter für öffentliche Programme von Kater, Beate Uwe, Ritter Butzke, Tanzhaus West und Gretchen (einschließlich Live-Auftritten).
- `event_curator/ui/`: HTML/CSS/JavaScript und lokale Kartenbasis für den interaktiven Report.
- `event_curator/featured.py`: kleine öffentliche Downtempo-Entdeckungsliste, getrennt von persönlichen Favoriten.
- `data/sample_artists.csv`: ausschließlich fiktive öffentliche Beispieldaten.
- `scripts/`: GitHub-Setup, Datenschutzprüfung und monatliche Ausführung.
- `scripts/scan_artist_pages.py`: lädt allgemeine Clubseiten und gleicht private Artist-Namen ausschließlich lokal ab; Hinweise sind keine bestätigten Gigs.
- `tests/`: Offline-Tests mit synthetischen Daten.
- `data/user_*`, `.env`, `exports/`: lokale, ignorierte Nutzerdaten; geprüfte Einzeltermine
  in `data/user_verified_events.json` werden bei Live-Läufen zusätzlich geladen.
- `data/user_sources.json`: lokale, ignorierte Liste weiterer Club- und Rechercheseiten.

## Versionierung
`event_curator/__init__.py` enthält `APP_VERSION`; CLI und Reports zeigen sie an.
Neue Versionen erst für stabile Releases; README und CHANGELOG dabei synchron halten.

## Entwicklung und neue Funktionen
Direkt auf `develop` arbeiten; `main` enthält stabile Releases. PRs und Releases nur nach Bestätigung.
Neue Quellen in `event_curator/sources/` ergänzen, CLI-Optionen in `event_curator/cli.py`.
Gemeinsame Filter bleiben im Matching-Modul. Regionalringe und Reiseländer sind getrennte
Rubriken; Reiseland-Events dürfen nur DE/FR/CH/AT und belastbare Städte enthalten.
Keine persönlichen Fixtures oder Keys in Tests.
Live-Berichte filtern nach belegtem Downtempo-/Melodic-Stil oder lokalen Artist-Treffern.
Kartengrenzen stammen aus Natural Earth (Public Domain); die generierte SVG wird mit `scripts/build_map_asset.py` gebaut und im Repo mitgeführt.
Vor Upload Datenschutzprüfung und Offline-Tests ausführen. Dokumentation auf Deutsch pflegen.
Recherchehinweise aus Clubs, Festivals und SoundCloud nicht ohne Datum-/Ortsprüfung in Events umdeuten.
Artist-Vorschläge nicht automatisch zu Favoriten machen. Die Recherche darf überregional sein,
der Monatsdigest muss den Regionsfilter behalten. Unbekannte Venue-Domains lokal konfigurieren.
