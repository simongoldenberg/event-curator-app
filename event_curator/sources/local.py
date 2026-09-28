import csv
from datetime import datetime
from pathlib import Path
from ..models import Event
from ..storage import read_json


def load_local(path):
    path = Path(path)
    if not path.exists():
        raise ValueError("Lokale Eventdatei wurde nicht gefunden.")
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    else:
        rows = read_json(path)
    if not isinstance(rows, list):
        raise ValueError("Eventdatei muss eine Liste enthalten.")
    return [Event.from_dict(row) for row in rows]


def sample_events(month):
    rows = [
        ("Example Dusk Ensemble – Live (FIKTIV)", "Würzburg", "DE", "live", "Example Dusk Ensemble", "Downtempo", 49.79, 9.95),
        ("Organic Garden Open Air (FIKTIV)", "Freiburg", "DE", "party", "Example Forest Circuit", "Organic House;Slow Rave;Open Air", 48.0, 7.84),
        ("Hypnotic Clubnacht (FIKTIV)", "Wien", "AT", "party", "Example Concrete Pulse", "Berlin Techno;Hypnotic;Club", 48.21, 16.37),
        ("Downtempo Garden Session (FIKTIV)", "Berlin", "DE", "party", "Example Dusk Ensemble", "Downtempo;Open Air", 52.52, 13.4),
        ("Mainufer Slow Rave (FIKTIV)", "Frankfurt", "DE", "party", "Example Forest Circuit", "Slow Rave;Organic House", 50.11, 8.68),
    ]
    return [Event.from_dict({"title": title, "start": f"{month}-28T20:00:00", "city": city,
                            "country": country, "category": category, "artists": artist,
                            "tags": tags, "latitude": lat, "longitude": lon,
                            "venue": "Fiktive Beispiel-Location"}, "Offline-Beispiel")
            for title, city, country, category, artist, tags, lat, lon in rows]
