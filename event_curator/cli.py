import argparse
from datetime import date, timedelta
import os
from pathlib import Path
import re
import sys
from config import DATA, DEFAULT_RADIUS_KM, EXPORTS, PROFILE, REGIONS, ROOT, SOURCES, STATE, load_env, radius_for_region
from . import APP_VERSION
from .discovery import page_hints, write_discovery
from .interview import interview, validate_profile
from .matching import match_events
from .reports import write_digest
from .sources.bandsintown import fetch_artist
from .sources.clubs import CLUBS, fetch_club
from .sources.goabase import fetch_country, fetch_region, TRAVEL_COUNTRIES
from .sources.http import HttpClient, SourceError
from .sources.local import load_local, sample_events
from .sources.structured import fetch_site
from .spotify import import_spotify
from .storage import read_artists, read_json, write_json
from .venue_catalog import read_venues


def month_bounds(value):
    if not re.fullmatch(r"\d{4}-\d{2}", value):
        raise ValueError("Monat muss YYYY-MM sein.")
    start = date.fromisoformat(value + "-01")
    end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return start, end


def template_sources():
    return {
        "sites": [],
        "research_pages": [
            {"name": "Waldschänke Dornheim Würzburg", "url": "https://waldschaenke-dornheim.de/club/", "enabled": True},
            {"name": "Airport Würzburg", "url": "https://club-airport.com/", "enabled": True},
            {"name": "Posthalle Würzburg", "url": "https://www.posthalle.de/programm/", "enabled": True},
            {"name": "E-Werk Erlangen", "url": "https://www.e-werk.de/programm/partys/", "enabled": True},
            {"name": "Die Rakete Nürnberg", "url": "https://dierakete.com/programm/", "enabled": True},
            {"name": "Kater (früher Kater Blau)", "url": "https://www.katerclub.de/", "enabled": True,
             "artist_section_start": "Residents", "artist_section_end": "Radio"},
            {"name": "Tanzhaus West", "url": "https://tanzhaus-west.de/", "enabled": True},
        ],
        "venue_sites": [],
    }


def run(args):
    load_env()
    if args.import_spotify:
        result = import_spotify(args.import_spotify, DATA / "user_artists.csv", args.replace_import)
        print(f"Spotify-Import: {result['plays']} Musikwiedergaben aus {result['files']} Audio-Dateien; "
              f"{result['artists']} Artists lokal gespeichert: {result['destination']}")
        return 0
    if args.init_sources:
        if SOURCES.exists():
            raise ValueError("Lokale Quellenkonfiguration existiert bereits; sie wurde nicht überschrieben.")
        write_json(SOURCES, template_sources())
        print(f"Lokale Quellenkonfiguration angelegt: {SOURCES}")
        return 0
    if args.interview:
        interview()
        return 0
    start, end = month_bounds(args.month)
    if args.monthly and not args.live:
        raise ValueError("--monthly erfordert --live; Beispielberichte markieren keinen Monatslauf als erledigt.")
    if args.discover and not args.live and not args.events:
        raise ValueError("--discover benötigt --live oder eine lokale --events-Datei.")
    if args.live and not args.include_bandsintown and args.artists:
        print("Künstlerliste wird nur lokal zum Matching verwendet. Bandsintown-Abfragen erfordern --include-bandsintown.")
    state = read_json(STATE, {}) if args.monthly else {}
    if not isinstance(state, dict):
        raise ValueError("Ungültiger Monatsstatus.")
    if args.monthly and not args.force and state.get(args.month, {}).get("success"):
        files = state[args.month].get("reports", [])
        if files and all(Path(path).is_file() for path in files):
            print(f"Monatslauf {args.month} bereits erfolgreich. Mit --force erneut ausführen.")
            return 0
    artist_path = Path(args.artists) if args.artists else next((p for p in (DATA / "artists.csv", DATA / "user_artists.csv") if p.exists()), DATA / "sample_artists.csv")
    artists = read_artists(artist_path)
    venues = read_venues()
    profile = validate_profile(read_json(PROFILE, {}))
    events, warnings, statuses, pages = [], [], [], []
    if artist_path.resolve() != (DATA / "sample_artists.csv").resolve():
        statuses.append(f"Lokales Musikprofil: {len(artists)} Künstler für das Matching geladen.")
    if not PROFILE.exists():
        warnings.append("Kein Party-Profil: Downtempo-/Melodic-Fokus und Standardregionen werden verwendet.")
    demo = not args.live and not args.events
    if demo:
        events = sample_events(args.month)
        statuses.append("Offline-Beispiel: ausschließlich fiktive Events, keine Netzwerkanfragen.")
    if args.events:
        imported = load_local(Path(args.events))
        events.extend(imported)
        statuses.append(f"Lokaler Eventimport: {len(imported)} Datensätze.")
    verified = DATA / "user_verified_events.json"
    if args.live and verified.exists() and not args.events:
        imported = load_local(verified)
        events.extend(imported)
        statuses.append(f"Lokal geprüfte Artist-Termine: {len(imported)} Datensätze.")
    failed = False
    if args.live:
        client = HttpClient()
        if not args.no_clubs:
            for club in CLUBS:
                if club["city"] not in (profile.get("regions") or list(REGIONS)):
                    continue
                try:
                    found, notes = fetch_club(client, club, args.month)
                    events.extend(found)
                    warnings.extend(notes)
                    failed |= any("keine auswertbaren Events" not in note for note in notes)
                    statuses.append(f"Clubprogramm / {club['name']}: {len(found)} Termine.")
                except (SourceError, ValueError, KeyError, TypeError) as exc:
                    failed = True
                    warnings.append(f"Clubprogramm / {club['name']}: {exc if isinstance(exc, SourceError) else 'Ungültiges Datenformat.'}")
        for region in profile.get("regions") or list(REGIONS):
            try:
                found, notes = fetch_region(client, region, args.month, radius_for_region(region, profile))
                events.extend(found)
                warnings.extend(notes)
                failed |= bool(notes)
                statuses.append(f"Goabase / {region}: {len(found)} Datensätze.")
            except (SourceError, ValueError, KeyError, TypeError) as exc:
                failed = True
                warnings.append(f"Goabase / {region}: {exc if isinstance(exc, SourceError) else 'Ungültiges Datenformat.'}")
        for country in TRAVEL_COUNTRIES:
            try:
                found, notes = fetch_country(client, country, args.month)
                events.extend(found)
                warnings.extend(notes)
                failed |= bool(notes)
                statuses.append(f"Goabase / Reiseland {country}: {len(found)} Datensätze.")
            except (SourceError, ValueError, KeyError, TypeError) as exc:
                failed = True
                warnings.append(f"Goabase / Reiseland {country}: {exc if isinstance(exc, SourceError) else 'Ungültiges Datenformat.'}")
        if args.include_bandsintown:
            app_id = os.environ.get("BANDSINTOWN_APP_ID", "")
            if not app_id or artist_path.resolve() == (DATA / "sample_artists.csv").resolve():
                warnings.append("Bandsintown benötigt eine eigene App-ID und eine eigene Künstler-CSV.")
                failed = True
            else:
                print("Bandsintown: einzelne Künstlernamen werden für die API-Abfragen übertragen.")
                for artist in artists:
                    try:
                        query_start = start - timedelta(days=730) if args.discover else start
                        found = fetch_artist(client, artist, app_id, query_start, end - timedelta(days=1))
                        events.extend(found)
                        statuses.append(f"Bandsintown / {artist.name}: {len(found)} Datensätze.")
                    except (SourceError, ValueError, KeyError, TypeError, AttributeError):
                        warnings.append(f"Bandsintown / {artist.name}: Abfrage fehlgeschlagen; App-ID, Zugriff und Format prüfen.")
                        failed = True
        else:
            statuses.append("Bandsintown deaktiviert; Künstlernamen bleiben bei diesem Lauf lokal.")
        settings = read_json(SOURCES, {})
        if not isinstance(settings, dict):
            raise ValueError("Quellenkonfiguration muss ein JSON-Objekt sein.")
        for site in settings.get("sites", []):
            if not site.get("enabled", True):
                continue
            found, notes = fetch_site(client, site)
            events.extend(found)
            warnings.extend(notes)
            failed |= bool(notes)
            statuses.append(f"{site['name']}: {len(found)} strukturierte Events.")
        if args.discover:
            # Nur bekannte, lokal konfigurierte Club-Domains nachladen: keine erratenen Websites.
            from .discovery import venue_network
            discovered_venues, _ = venue_network(events, artists)
            known = {v["venue"].casefold() for v in discovered_venues}
            for site in settings.get("venue_sites", []):
                if site.get("enabled", True) and site.get("venue", "").casefold() in known:
                    found, notes = fetch_site(client, site)
                    events.extend(found)
                    warnings.extend(notes)
                    failed |= bool(notes)
            for page in settings.get("research_pages", []):
                if not page.get("enabled", True):
                    continue
                try:
                    pages.append(page_hints(client, page))
                except (SourceError, ValueError, KeyError, TypeError) as exc:
                    warnings.append(f"{page.get('name', 'Recherchequelle')}: {exc if isinstance(exc, SourceError) else 'Ungültige Konfiguration.'}")
                    failed = True
        if not settings.get("sites"):
            warnings.append("Keine zusätzlichen maschinenlesbaren Event-Seiten konfiguriert; Recherche-Seiten liefern nur Hinweise.")
    output = Path(args.output).resolve()
    if not output.is_relative_to(EXPORTS.resolve()):
        raise ValueError("Berichte dürfen zum Schutz vor Git-Uploads nur unter exports/ liegen.")
    if args.discover:
        print(f"Recherche: {write_discovery(events, artists, pages, DATA, output, warnings)}")
    # Die fiktive Beispiel-CSV darf echte Live-Termine nicht über beliebige Genres hochstufen.
    matching_artists = [] if args.live and artist_path.resolve() == (DATA / "sample_artists.csv").resolve() else artists
    matches = match_events(events, matching_artists, profile, start, end, today=start if demo else None,
                           focused=args.live or bool(args.events), travel=args.live or bool(args.events))
    paths = write_digest(matches, args.month, output, warnings, statuses, demo,
                         profile.get("radius_km", DEFAULT_RADIUS_KM), venues)
    print(f"Event Curator {APP_VERSION}: {len(matches)} Funde, {len(venues)} recherchierte Venues")
    for path in paths:
        print(path)
    for warning in dict.fromkeys(warnings):
        print(f"Hinweis: {warning}", file=sys.stderr)
    if args.monthly and not failed:
        state[args.month] = {"success": True, "reports": [str(p) for p in paths], "completed": date.today().isoformat()}
        write_json(STATE, state)
    return 2 if failed else 0


def main(argv=None):
    # Auch umgeleitete Windows-Konsolen sollen Eventnamen mit Unicode ausgeben können.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")
    parser = argparse.ArgumentParser(description="Lokales Event- & Party-Tracking; ohne Optionen: Offline-Beispiel.")
    parser.add_argument("--version", action="version", version=APP_VERSION)
    parser.add_argument("--interview", action="store_true", help="Lokales Präferenzinterview")
    parser.add_argument("--import-spotify", metavar="ORDNER", help="Spotify-Audio-Historie lokal auswerten und private Künstlerliste anlegen")
    parser.add_argument("--replace-import", action="store_true", help="Eine bestehende importierte Künstlerliste ersetzen")
    parser.add_argument("--init-sources", action="store_true", help="Lokale Quellenkonfiguration anlegen")
    parser.add_argument("--live", action="store_true", help="Clubprogramme, Goabase und konfigurierte Seiten abfragen")
    parser.add_argument("--no-clubs", action="store_true", help="Öffentliche Clubprogramme bei diesem Live-Lauf auslassen")
    parser.add_argument("--include-bandsintown", action="store_true", help="Einzelne Künstlernamen an Bandsintown übertragen (App-ID nötig)")
    parser.add_argument("--discover", action="store_true", help="Frühere Venues, ähnliche Artists und Gig-Hinweise recherchieren")
    parser.add_argument("--artists", help="Lokale Künstler-CSV")
    parser.add_argument("--events", help="Lokale Event-JSON/CSV")
    parser.add_argument("--month", default=date.today().strftime("%Y-%m"), help="Berichtsmonat YYYY-MM")
    parser.add_argument("--output", default=str(EXPORTS), help="Zielordner innerhalb exports/")
    parser.add_argument("--monthly", action="store_true", help="Erfolgreichen Monatslauf lokal merken")
    parser.add_argument("--force", action="store_true", help="Monatslauf wiederholen")
    args = parser.parse_args(argv)
    if args.include_bandsintown and not args.live:
        parser.error("--include-bandsintown erfordert --live")
    try:
        return run(args)
    except (KeyboardInterrupt, EOFError):
        print("\nAbgebrochen; bestehendes Profil bleibt erhalten.", file=sys.stderr)
        return 130
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (ValueError, OSError, KeyError, TypeError, AttributeError, SourceError):
        # Kein Traceback mit URLs, Profilinhalten oder API-Schlüsseln.
        print("Eingabe-/Dateifehler: CSV-Spalten, JSON-Konfiguration, Monat und Dateipfade prüfen (siehe README).", file=sys.stderr)
        return 1
