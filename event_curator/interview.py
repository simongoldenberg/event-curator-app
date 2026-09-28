from config import PROFILE, REGIONS, DEFAULT_RADIUS_KM
from .storage import write_json

GENRES = ["Organic Downtempo", "Slow Rave", "Berlin Techno", "Melodic", "Hypnotic", "Psy-Techno", "Organic House"]
CONCEPTS = ["Open Air", "Kollektiv", "Underground", "Off-Location", "Intime Clubnacht", "Festival"]
VENUES = ["Kater Blau", "Die Bucht", "Fusion", "Mystic Creatures", "Moyn"]


def choose(prompt, options, input_fn=input, output=print):
    output(prompt)
    for number, option in enumerate(options, 1):
        output(f"  {number}. {option}")
    while True:
        raw = input_fn("Nummern mit Komma, Enter = keine Auswahl: ").strip()
        if not raw:
            return []
        try:
            indices = list(dict.fromkeys(int(v.strip()) for v in raw.split(",")))
            if any(i < 1 or i > len(options) for i in indices):
                raise ValueError
            return [options[i - 1] for i in indices]
        except ValueError:
            output("Bitte gültige Nummern aus der Liste eingeben.")


def interview(path=PROFILE, input_fn=input, output=print):
    output("Party-Profil: Antworten werden ausschließlich lokal gespeichert.")
    genres = choose("Welche Genres/Vibes magst du?", GENRES, input_fn, output)
    concepts = choose("Welche Event-Konzepte passen zu dir?", CONCEPTS, input_fn, output)
    venues = choose("Welche Orte/Festivals dienen als Vibe-Referenz?", VENUES, input_fn, output)
    regions = choose("Welche Zielregionen? (Enter = alle drei)", list(REGIONS), input_fn, output) or list(REGIONS)
    while True:
        raw = input_fn(f"Suchradius je Region in km [Standard {DEFAULT_RADIUS_KM}, 1–200]: ").strip()
        try:
            radius = int(raw) if raw else DEFAULT_RADIUS_KM
            if not 1 <= radius <= 200:
                raise ValueError
            break
        except ValueError:
            output("Bitte eine ganze Zahl zwischen 1 und 200 eingeben.")
    excludes = [s.strip() for s in input_fn("Unerwünschte Begriffe, mit Komma getrennt (optional): ").split(",") if s.strip()]
    profile = {"schema_version": 1, "genres": genres, "concepts": concepts, "venue_references": venues,
               "regions": regions, "radius_km": radius, "exclude": excludes}
    write_json(path, profile)
    output(f"Profil gespeichert: {path}")
    return profile


def validate_profile(profile):
    if not isinstance(profile, dict):
        raise ValueError("Das Profil muss ein JSON-Objekt sein.")
    for key in ("genres", "concepts", "venue_references", "exclude", "regions"):
        if key in profile and (not isinstance(profile[key], list) or not all(isinstance(v, str) for v in profile[key])):
            raise ValueError(f"Profilfeld {key} muss eine Textliste sein.")
    if any(region not in REGIONS for region in profile.get("regions", [])):
        raise ValueError("Unbekannte Region im Profil.")
    radius = profile.get("radius_km", DEFAULT_RADIUS_KM)
    if not isinstance(radius, (int, float)) or not 1 <= radius <= 200:
        raise ValueError("Suchradius muss zwischen 1 und 200 km liegen.")
    return profile

