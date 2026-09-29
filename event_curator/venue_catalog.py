"""Lokal recherchierte Venue-Hinweise; Beziehungen zu Hörprofilen bleiben privat."""
from config import DATA
from .sources.http import safe_url
from .storage import read_json

CATALOG = DATA / "user_venues.json"
COUNTRIES = {"DE", "FR", "CH", "AT"}


def read_venues():
    rows = read_json(CATALOG, [])
    if not isinstance(rows, list):
        raise ValueError("Venue-Liste muss ein JSON-Array sein.")
    venues = []
    for row in rows:
        if not isinstance(row, dict) or not all(isinstance(row.get(k), str) and row[k].strip()
                                                for k in ("name", "city", "country", "url", "evidence_url")):
            continue
        if row["country"] not in COUNTRIES or not safe_url(row["url"]) or not safe_url(row["evidence_url"]):
            continue
        artists = row.get("artists", [])
        if not isinstance(artists, list) or not all(isinstance(a, str) for a in artists):
            continue
        venues.append({k: row[k] for k in ("name", "city", "country", "url", "evidence_url")}
                      | {"artists": artists, "latitude": row.get("latitude"),
                         "longitude": row.get("longitude")})
    return venues
