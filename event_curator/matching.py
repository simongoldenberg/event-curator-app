from dataclasses import dataclass
from datetime import date
from math import asin, cos, radians, sin, sqrt
from config import REGIONS, radius_for_region
from .featured import FEATURED_ARTISTS
from .models import normalized

# Transparente, heuristische Begriffe; keine Behauptung über tatsächliche Clubprogramme.
ALIASES = {
    "organic downtempo": ["downtempo", "organic downtempo"],
    "berlin techno": ["techno"], "psy techno": ["psy techno", "psytech", "psytechno"],
    "open air": ["open air", "openair", "outdoor"], "kollektiv": ["kollektiv", "collective"],
    "off location": ["off location", "warehouse"], "intime clubnacht": ["club", "clubnacht", "intimate"],
    "festival": ["festival"],
}
VENUE_HINTS = {
    "Kater Blau": ["organic house", "downtempo", "melodic"],
    "Die Bucht": ["open air", "downtempo"], "Fusion": ["festival", "collective", "kollektiv"],
    "Mystic Creatures": ["psy techno", "psytech", "hypnotic"], "Moyn": ["slow rave", "downtempo", "festival"],
}
TRAVEL_COUNTRIES = {"DE": "Deutschland", "FR": "Frankreich", "CH": "Schweiz", "AT": "Österreich"}
# Die stärkste belegte Stilübereinstimmung zählt einmal. Ein bloßer Clubname ist kein Genrebeleg.
FOCUS_STYLES = (
    ("organic downtempo", 38), ("downtempo", 35), ("downtechno", 35),
    ("ketapop", 35), ("slow rave", 32), ("slow house", 30),
    ("melodic techno", 32), ("melodic house", 28),
    ("organic house", 28), ("hypnotic techno", 25), ("psy techno", 25),
    ("melodic", 18), ("deep house", 18),
)


def contains(text, term):
    return f" {normalized(term)} " in f" {normalized(text)} "


def distance_km(lat1, lon1, lat2, lon2):
    a, b, c, d = map(radians, (lat1, lon1, lat2, lon2))
    h = sin((c-a)/2)**2 + cos(a)*cos(c)*sin((d-b)/2)**2
    return 6371.0088 * 2 * asin(sqrt(min(1, max(0, h))))


def region_match(event, profile):
    matches = []
    for name in profile.get("regions") or list(REGIONS):
        lat, lon, country, aliases = REGIONS[name]
        if event.latitude is not None and event.longitude is not None:
            distance = distance_km(lat, lon, event.latitude, event.longitude)
            if distance <= radius_for_region(name, profile):
                matches.append((distance, name, f"{distance:.0f} km Luftlinie"))
        elif event.country in (country, {"DE": "GERMANY", "AT": "AUSTRIA"}[country]) and normalized(event.city) in {normalized(a) for a in aliases}:
            matches.append((0, name, "Stadtname + Land; Entfernung unbekannt"))
    if not matches:
        return None
    _, name, detail = min(matches)
    return name, detail


@dataclass
class Match:
    event: object
    score: int
    reasons: list[str]
    region: str
    distance: str
    scope: str = "regional"


def match_events(events, artists, profile, start, end, today=None, focused=False, travel=False):
    today = today or date.today()
    result, seen = [], set()
    for event in events:
        event_end = event.end.date() if event.end else event.start.date()
        if event.start.date() >= end or event_end < max(start, today):
            continue
        if any(term in normalized(event.status) for term in ("cancel", "postpon", "abgesagt", "verschoben")):
            continue
        region = region_match(event, profile)
        scope = "regional"
        if not region:
            country = event.country.upper()
            if not travel or country not in TRAVEL_COUNTRIES or not event.city.strip():
                continue
            region = (TRAVEL_COUNTRIES[country], "außerhalb der lokalen Suchregionen")
            scope = "reise"
        text = " ".join([event.title, event.description, event.venue, *event.tags, *event.artists])
        if any(contains(text, word) for word in profile.get("exclude", []) if word.strip()):
            continue
        key = (normalized(event.title), event.start.isoformat(), normalized(event.city), normalized(event.venue))
        if key in seen:
            continue
        seen.add(key)
        score, reasons = 0, []
        music_evidence = False
        for artist in artists:
            if any(normalized(artist.name) == normalized(a) for a in event.artists) or contains(event.title + " " + event.description, artist.name):
                score += 50
                reasons.append(f"Künstler: {artist.name}")
                music_evidence = True
        for artist in FEATURED_ARTISTS:
            if any(normalized(artist.name) == normalized(a) for a in event.artists) or contains(event.title + " " + event.description, artist.name):
                if not any(normalized(artist.name) == normalized(a.name) for a in artists):
                    score += 14
                    reasons.append(f"Downtempo-Radar: {artist.name}")
                    music_evidence = True
        style = next(((term, points) for term, points in FOCUS_STYLES if contains(text, term)), None)
        if style:
            score += style[1]
            reasons.append(f"Sound: {style[0]}")
            music_evidence = True
        genre_prefs = list(dict.fromkeys(profile.get("genres", []) + [g for a in artists for g in a.genres]))
        for pref in genre_prefs + profile.get("concepts", []):
            if any(contains(text, term) for term in ALIASES.get(normalized(pref), [pref])):
                score += 10
                reasons.append(f"Begriff: {pref}")
                if pref in profile.get("genres", []):
                    music_evidence = True
        for venue in profile.get("venue_references", []):
            if any(contains(text, term) for term in VENUE_HINTS.get(venue, [])):
                score += 3
                reasons.append(f"Vibe-Heuristik: {venue}")
        if focused and not music_evidence:
            continue
        if not reasons:
            reasons.append("Regionaler Fund ohne belegte Präferenzübereinstimmung")
        result.append(Match(event, score, reasons, *region, scope))
    return sorted(result, key=lambda m: (-m.score, m.event.start.isoformat(), m.event.title))
