from urllib.parse import quote, urlencode
from ..models import Event
from .http import SourceError


def fetch_artist(client, artist, app_id, start, end):
    query = urlencode({"app_id": app_id, "date": f"{start.isoformat()},{end.isoformat()}"})
    url = f"https://rest.bandsintown.com/artists/{quote(artist.name, safe='')}/events?{query}"
    rows = client.json(url)
    if not isinstance(rows, list):
        raise SourceError("Bandsintown: unerwartete Antwort; App-ID und Künstlerzugriff prüfen.")
    events = []
    for row in rows:
        venue = row.get("venue") or {}
        events.append(Event.from_dict({
            "title": row.get("title") or f"{artist.name} – Live",
            "start": row["datetime"], "city": venue.get("city", ""),
            "country": venue.get("country", ""), "venue": venue.get("name", ""),
            "latitude": venue.get("latitude"), "longitude": venue.get("longitude"),
            "artists": row.get("lineup") or [artist.name], "category": "live",
            "description": row.get("description", ""), "url": row.get("url", ""),
        }, "Bandsintown"))
    return events

