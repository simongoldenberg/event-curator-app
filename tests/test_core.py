from datetime import date, datetime
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from event_curator.cli import month_bounds, main
from event_curator.discovery import venue_network, page_hints
from event_curator.interview import interview, validate_profile
from event_curator.matching import match_events, region_match
from config import DEFAULT_RADIUS_KM, REGIONS
from event_curator.models import Artist, Event, coordinate
from event_curator.reports import write_digest
from event_curator.sources.bandsintown import fetch_artist
from event_curator.sources.clubs import CLUBS, beate_events, document, kater_events, ritter_events, tanzhaus_events
from event_curator.sources.goabase import fetch_country, fetch_region
from event_curator.sources.http import SourceError, safe_url
from event_curator.sources.structured import fetch_site
from event_curator.storage import read_artists, read_json
from event_curator.spotify import MAX_ARTISTS, import_spotify
from event_curator.ui.dashboard import render_dashboard
from scripts.check_privacy import public_path, SECRET


def temporary_directory():
    root = Path(__file__).resolve().parents[1] / "exports" / "test-temp"
    root.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=root)


def event(**overrides):
    values = {"title": "Test", "start": datetime(2030, 5, 12, 21), "city": "Wien", "country": "AT", "venue": "Testclub"}
    values.update(overrides)
    return Event(**values)


class CoreTests(unittest.TestCase):
    def test_two_hundred_artists_and_travel_scope(self):
        self.assertEqual(MAX_ARTISTS, 200)
        nearby = event(title="Organic Downtempo in Wien")
        paris = event(title="Organic Downtempo in Paris", city="Paris", country="FR")
        outside = event(title="Organic Downtempo in Madrid", city="Madrid", country="ES")
        matches = match_events([nearby, paris, outside], [], {}, date(2030, 5, 1),
                               date(2030, 6, 1), today=date(2030, 5, 1), focused=True, travel=True)
        self.assertEqual({m.event.city: m.scope for m in matches}, {"Wien": "regional", "Paris": "reise"})
        venue = {"name": "Testclub", "city": "Paris", "country": "FR", "url": "https://example.org/programme",
                 "evidence_url": "https://example.org/beleg", "artists": ["Testartist"]}
        html = render_dashboard(matches, "2030-05", [], [], venues=[venue])
        self.assertIn('id="reisen"', html)
        self.assertIn('id="venues"', html)
        self.assertIn("Testclub", html)
        self.assertIn("Unterwegs in vier Ländern", html)

    def test_regions_and_unknown_coordinates(self):
        self.assertEqual(region_match(event(), {})[0], "Wien")
        self.assertIsNone(region_match(event(city="Vienna", country="US"), {}))
        self.assertIsNone(region_match(event(city="Wiener Neustadt"), {}))
        self.assertEqual(region_match(event(latitude=52.52, longitude=13.4), {})[0], "Berlin")
        self.assertIsNotNone(region_match(event(city="unbekannt", latitude=48.21, longitude=16.37), {}))
        self.assertIsNone(region_match(event(latitude=48.5, longitude=16.37), {"radius_km": 1}))

    def test_invalid_coordinate(self):
        for number in ("nan", "inf", "91"):
            with self.assertRaises(ValueError):
                coordinate(number, 90)

    def test_five_regions_and_fifty_kilometre_default(self):
        self.assertEqual(DEFAULT_RADIUS_KM, 50)
        self.assertEqual(set(REGIONS), {"Würzburg", "Freiburg", "Wien", "Berlin", "Frankfurt"})
        self.assertEqual(region_match(event(city="Frankfurt am Main", country="DE"), {})[0], "Frankfurt")
        self.assertIsNone(region_match(event(city="Testort", country="DE", latitude=48.58, longitude=7.8421), {}))

    def test_matching_dates_cancelled_exclusions_and_dedup(self):
        events = [event(title="Party", tags=["Downtempo"]), event(title="Party", tags=["Downtempo"]),
                  event(title="Abgesagt", status="https://schema.org/EventCancelled"),
                  event(title="Später", start=datetime(2030, 6, 1)),
                  event(title="Früher", start=datetime(2030, 4, 30)), event(title="Hardstyle")]
        found = match_events(events, [], {"genres": ["Organic Downtempo"], "exclude": ["Hardstyle"]}, date(2030, 5, 1), date(2030, 6, 1), today=date(2030, 5, 1))
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].score, 45)

    def test_festival_overlap_and_artist_boundary(self):
        events = [event(title="Festival", start=datetime(2030, 4, 30), end=datetime(2030, 5, 3), artists=["Annabel"])]
        found = match_events(events, [Artist("Anna")], {}, date(2030, 5, 1), date(2030, 6, 1), today=date(2030, 5, 1))
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].score, 0)

    def test_month_validation(self):
        self.assertEqual(month_bounds("2028-12")[1], date(2029, 1, 1))
        for value in ("2028-13", "../2030", "2030-1"):
            with self.assertRaises(ValueError):
                month_bounds(value)

    def test_csv_unicode_bom_duplicates(self):
        with temporary_directory() as folder:
            path = Path(folder) / "artists.csv"
            path.write_text("artist,genres\nÄther,Organic House;Downtempo\näther,Hypnotic\n", encoding="utf-8-sig")
            artists = read_artists(path)
            self.assertEqual(len(artists), 1)
            self.assertEqual(artists[0].genres, ["Hypnotic"])

    def test_interview_validation_and_atomic_abort(self):
        with temporary_directory() as folder:
            path = Path(folder) / "profile.json"
            replies = iter(["99", "1,2", "1", "1", "3", "0", "80", "Hardstyle"])
            profile = interview(path, lambda _: next(replies), lambda _: None)
            self.assertEqual(profile["radius_km"], 80)
            self.assertEqual(read_json(path)["regions"], ["Wien"])
            old = path.read_text()
            with self.assertRaises(EOFError):
                interview(path, lambda _: (_ for _ in ()).throw(EOFError()), lambda _: None)
            self.assertEqual(path.read_text(), old)

    def test_profile_validation(self):
        for profile in ({"regions": ["Hamburg"]}, {"radius_km": -1}, {"genres": "Techno"}):
            with self.assertRaises(ValueError):
                validate_profile(profile)

    def test_report_escapes_remote_content(self):
        unsafe = event(title="<script>alert(1)</script>", url="javascript:alert(1)")
        matches = match_events([unsafe], [], {}, date(2030, 5, 1), date(2030, 6, 1), today=date(2030, 5, 1))
        with temporary_directory() as folder:
            paths = write_digest(matches, "2030-05", Path(folder), [], [], False)
            html = paths[1].read_text(encoding="utf-8")
            self.assertNotIn("<script>alert(1)</script>", html)
            self.assertNotIn("javascript:", html)
            self.assertIn("Rubrik 1", html)
            self.assertIn("Rubrik 2", html)
            self.assertIn("&lt;script&gt;", html)
            self.assertIn('id="karte"', html)
            self.assertIn('id="map-pins"', html)
            self.assertIn('data-region-filter="Berlin"', html)
            self.assertIn("Downtempo-Radar", html)

    def test_featured_artist_is_distinct_from_favorite(self):
        featured = event(title="Acid Pauli Live")
        found = match_events([featured], [], {}, date(2030, 5, 1), date(2030, 6, 1), today=date(2030, 5, 1))
        self.assertEqual(found[0].score, 14)
        favorite = match_events([featured], [Artist("Acid Pauli")], {}, date(2030, 5, 1), date(2030, 6, 1), today=date(2030, 5, 1))
        self.assertEqual(favorite[0].score, 50)

    def test_focused_matching_prefers_melodic_and_excludes_unrelated_goa(self):
        events = [event(title="Melodic Techno Nacht"), event(title="Goa Trance Nacht"),
                  event(title="Beate Barfuß", tags=["Downtempo"])]
        found = match_events(events, [], {}, date(2030, 5, 1), date(2030, 6, 1),
                             today=date(2030, 5, 1), focused=True)
        self.assertEqual({m.event.title for m in found}, {"Melodic Techno Nacht", "Beate Barfuß"})
        self.assertGreater(found[0].score, 0)

    def test_club_pages_parse_dates_and_own_evidence(self):
        kater = '''<article id="event-7" class="event"><span class="date-title">Katernacht</span>
          <div class="entry-summary"><p>Fr. 02.10 22:00 – Sa. 03.10 08:00</p><p>Acid Pauli<br>Open Air</p></div></article>'''
        parsed = kater_events(document(kater), CLUBS[0], 2030, 10)
        self.assertEqual(len(parsed), 1)
        self.assertIn("Acid Pauli", parsed[0].description)
        self.assertEqual(parsed[0].start.hour, 22)
        self.assertEqual(parsed[0].venue, "Kater")
        beate = '''<span class="elementor-icon-list-text">FR, 02.10.30 OKT</span>
          <span class="elementor-icon-list-text">23:00</span><p>Beate Barfuß</p><p>w/ Just Emma</p>
          <span class="elementor-icon-list-text">SA, 03.10.30 OKT</span>
          <span class="elementor-icon-list-text">21:00</span><p>Andere Nacht</p>'''
        parsed = beate_events(document(beate), CLUBS[1], 2030, 10)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0].tags, ["Downtempo"])
        self.assertNotIn("Andere Nacht", parsed[0].description)
        listing = '''<div class="cm_thw_events_list"><h1>Oktober</h1></div>
          <div class="cm_thw_events_list event"><div class="content-left">Fr /02</div>
          <div class="content-right"><a href="/veranstaltungen/nacht/"><h2>Nacht</h2><p>Melodic Techno</p></a></div></div>'''
        class Client:
            def page(self, url):
                return '<div class="event_detail"><p>Ab 23 Uhr</p><p>mit Live Act</p></div>'
        parsed, notes = tanzhaus_events(Client(), document(listing), CLUBS[2], 2030, 10)
        self.assertEqual(notes, [])
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].start.hour, 23)
        self.assertIn("Melodic Techno", parsed[0].description)
        ritter = '<div><a class="event-link" href="/event/test">Details</a><span>20.11.30</span><h2>Mollono.Bass</h2></div>'
        class RitterClient:
            def page(self, url):
                return '<h1>Mollono.Bass</h1><p>20.11.2030 ab 22:00 Line Up: MOLLONO.BASS</p><p>For fans of: Oliver Koletzki</p>'
        parsed, notes = ritter_events(RitterClient(), document(ritter), CLUBS[3], 2030, 11)
        self.assertEqual(notes, [])
        self.assertEqual(len(parsed), 1)
        self.assertNotIn("Oliver Koletzki", parsed[0].description)

    def test_spotify_import_keeps_only_music_and_writes_private_artist_summary(self):
        with temporary_directory() as folder:
            root = Path(folder)
            audio = [
                {"ts": "2023-05-01T12:00:00Z", "spotify_track_uri": "spotify:track:a", "master_metadata_album_artist_name": "Alt", "ms_played": 300000},
                {"ts": "2025-05-01T12:00:00Z", "spotify_track_uri": "spotify:track:b", "master_metadata_album_artist_name": "Neu", "ms_played": 300000},
                {"ts": "2025-05-02T12:00:00Z", "spotify_track_uri": "spotify:track:c", "master_metadata_album_artist_name": "Übersprungen", "ms_played": 5000},
                {"ts": "2025-05-03T12:00:00Z", "spotify_episode_uri": "spotify:episode:a", "master_metadata_album_artist_name": None, "ms_played": 300000},
            ]
            (root / "Streaming_History_Audio_2025.json").write_text(json.dumps(audio), encoding="utf-8")
            (root / "Streaming_History_Audio_2025_1.json").write_text(json.dumps([audio[1]]), encoding="utf-8")
            (root / "Streaming_History_Video_2025.json").write_text(json.dumps(audio), encoding="utf-8")
            destination = root / "artists.csv"
            result = import_spotify(root, destination)
            self.assertEqual((result["files"], result["plays"], result["artists"]), (2, 2, 2))
            self.assertEqual([a.name for a in read_artists(destination)], ["Neu", "Alt"])
            self.assertNotIn("spotify:track", destination.read_text(encoding="utf-8"))
            with self.assertRaises(FileExistsError):
                import_spotify(root, destination)

    def test_discovery_network_keeps_favorites_separate(self):
        old = event(start=datetime(2020, 1, 1), artists=["Favorite", "New Artist"], url="https://example.org/old")
        future = event(artists=["Another Artist"])
        venues, artists = venue_network([old, future], [Artist("Favorite")])
        self.assertEqual(len(venues), 1)
        self.assertEqual({a["artist"] for a in artists}, {"New Artist", "Another Artist"})

    def test_bandsintown_url_and_normalization(self):
        class Client:
            def json(self, url):
                self.url = url
                return [{"datetime": "2030-05-12T21:00:00", "venue": {"city": "Vienna", "country": "Austria"}}]
        client = Client()
        events = fetch_artist(client, Artist("A/B & C"), "test", date(2030, 5, 1), date(2030, 5, 31))
        self.assertIn("A%2FB%20%26%20C", client.url)
        self.assertEqual(events[0].category, "live")
        self.assertIsNotNone(region_match(events[0], {}))

    def test_goabase_details_and_empty(self):
        row = {"id": 1, "nameParty": "Test", "dateStart": "2030-05-12T21:00:00+02:00", "nameTown": "Wien", "isoCountry": "AT", "urlPartyHtml": "https://www.goabase.net/party/test/1"}
        class Client:
            def json(self, url, **kwargs):
                return {"partylist": [row]} if "?" in url else {"party": {**row, "textLineUp": "Favorite"}}
        events, notes = fetch_region(Client(), "Wien", "2030-05")
        self.assertEqual(events[0].description.strip(), "Favorite")
        self.assertEqual(events[0].url, row["urlPartyHtml"])
        self.assertEqual(notes, [])

    def test_structured_pages_and_graph(self):
        page = '''<a href="/events/1">event</a><a href="https://elsewhere.example/events/2">other</a>'''
        detail = '''<script type="application/ld+json">{"@graph":[{"@type":"DanceEvent","name":"Night","startDate":"2030-05-12T21:00:00","location":{"name":"Club","address":{"addressLocality":"Wien","addressCountry":"AT"}},"performer":[{"name":"Example"}]}]}</script>'''
        class Client:
            def page(self, url):
                return detail if url.endswith("/1") else page
        events, notes = fetch_site(Client(), {"name": "Club", "url": "https://example.org/"})
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].artists, ["Example"])
        self.assertEqual(notes, [])

    def test_blocked_site_visible(self):
        class Client:
            def page(self, url):
                raise SourceError("HTTP 403")
        events, notes = fetch_site(Client(), {"name": "Club", "url": "https://example.org/"})
        self.assertEqual(events, [])
        self.assertTrue(any("403" in note for note in notes))

    def test_soundcloud_hydration_hints(self):
        class Client:
            def page(self, url):
                return '<script>window.__sc_hydration = [{"data":{"description":"Upcoming gigs: 12.05. Club"}}];</script>'
        hints = page_hints(Client(), {"name": "Artist", "url": "https://soundcloud.com/example"})
        self.assertIn("Upcoming gigs: 12.05. Club", hints["hints"])

    def test_club_resident_candidates(self):
        class Client:
            def page(self, url):
                return '<h1>Residents</h1><h2>Example Artist</h2><h1>Radio</h1><p>Unrelated</p>'
        hints = page_hints(Client(), {"name": "Club", "url": "https://example.org/", "artist_section_start": "Residents", "artist_section_end": "Radio"})
        self.assertEqual(hints["artist_candidates"], ["Example Artist"])

    def test_partial_month_does_not_mark_complete(self):
        with temporary_directory() as folder:
            root = Path(folder)
            with patch("event_curator.cli.EXPORTS", root), patch("event_curator.cli.PROFILE", root / "missing.json"), patch("event_curator.cli.SOURCES", root / "missing.json"), patch("event_curator.cli.STATE", root / "state.json"), patch("event_curator.cli.fetch_region", side_effect=SourceError("HTTP 503")):
                result = main(["--live", "--no-clubs", "--monthly", "--month", "2030-05", "--output", str(root)])
            self.assertEqual(result, 2)
            self.assertFalse((root / "state.json").exists())
            self.assertIn("503", (root / "digest-2030-05.md").read_text(encoding="utf-8"))

    def test_month_success_and_repeat(self):
        with temporary_directory() as folder:
            root = Path(folder)
            with patch("event_curator.cli.EXPORTS", root), patch("event_curator.cli.PROFILE", root / "missing.json"), patch("event_curator.cli.SOURCES", root / "missing.json"), patch("event_curator.cli.STATE", root / "state.json"), patch("event_curator.cli.fetch_region", return_value=([], [])) as fetch:
                argv = ["--live", "--no-clubs", "--monthly", "--month", "2030-05", "--output", str(root)]
                self.assertEqual(main(argv), 0)
                self.assertEqual(main(argv), 0)
                self.assertEqual(fetch.call_count, 5)

    def test_privacy_allowlist_and_secret(self):
        self.assertTrue(public_path("data/sample_artists.csv"))
        self.assertTrue(public_path("event_curator/cli.py"))
        for path in ("data/artists.csv", ".env", "exports/report.md", "user_profile.py", "tests/user_profile.py"):
            self.assertFalse(public_path(path))
        self.assertIsNotNone(SECRET.search(b"BANDSINTOWN_APP_ID=" + b"dummy-key"))
        self.assertIsNone(SECRET.search(b"BANDSINTOWN_APP_ID=\n"))
        self.assertIsNone(SECRET.search(b"BANDSINTOWN_APP_ID=\n```\n"))

    def test_url_validation(self):
        self.assertTrue(safe_url("https://example.org/event"))
        for url in ("javascript:alert(1)", "https://user:pass@example.org/", "http://example.org/", "https://example.org/\n"):
            self.assertFalse(safe_url(url))

    def test_cli_demo_without_network(self):
        with temporary_directory() as folder:
            root = Path(folder)
            with patch("event_curator.cli.EXPORTS", root), patch("event_curator.cli.HttpClient", side_effect=AssertionError("Network in demo")):
                result = main(["--month", "2030-05", "--output", str(root)])
            self.assertEqual(result, 0)
            self.assertTrue((root / "digest-2030-05-demo.html").exists())


if __name__ == "__main__":
    unittest.main()
