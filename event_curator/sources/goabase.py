from urllib.parse import urlencode
from config import REGIONS, DEFAULT_RADIUS_KM
from ..models import Event, terms
from .http import SourceError

TRAVEL_COUNTRIES = ("DE", "FR", "CH", "AT")


def fetch_country(client, country, month):
    """Liest die öffentlichen Monatslisten; Detailabrufe bleiben der Regionalsuche vorbehalten."""
    if country not in TRAVEL_COUNTRIES:
        raise ValueError("Unbekanntes Reiseland.")
    query = urlencode({"country": country, "limit": 500, "searchdate": month})
    payload = client.json("https://www.goabase.net/api/party/json/?" + query, empty_on_404=True)
    if payload is None:
        return [], []
    rows = payload.get("partylist") if isinstance(payload, dict) else payload
    if isinstance(rows, dict):
        rows = [rows] if "nameParty" in rows else list(rows.values())
    if not isinstance(rows, list):
        raise SourceError("Goabase: unbekanntes Antwortformat.")
    warnings = [f"Goabase / {country}: 500er-Limit erreicht; Reiseland eventuell unvollständig."] if len(rows) >= 500 else []
    events = []
    for row in rows:
        try:
            events.append(parse_party(row))
        except (ValueError, KeyError, TypeError, AttributeError):
            warnings.append(f"Goabase / {country}: ungültigen Datensatz übersprungen.")
    return events, list(dict.fromkeys(warnings))


def parse_party(row):
    return Event.from_dict({
        "title": row["nameParty"], "start": row["dateStart"], "end": row.get("dateEnd"),
        "city": row.get("nameTown", ""), "country": row.get("isoCountry", ""),
        "venue": row.get("nameLocation", ""), "latitude": row.get("geoLat"), "longitude": row.get("geoLon"),
        "category": "party", "tags": [row.get("nameType", ""), *terms(row.get("keywords"))],
        "description": " ".join(str(row.get(k) or "") for k in ("textLineUp", "textMore", "textLocation")),
        "url": row.get("urlPartyHtml") or row.get("urlParty", ""), "status": row.get("nameStatus", "scheduled"),
    }, "Goabase" )


def fetch_region(client, name, month, radius=DEFAULT_RADIUS_KM):
    lat, lon, _, _ = REGIONS[name]
    query = urlencode({"ll": f"{lat},{lon}", "radius": max(50, radius), "limit": 500, "searchdate": month})
    payload = client.json("https://www.goabase.net/api/party/json/?" + query, empty_on_404=True)
    if payload is None:
        return [], []
    rows = payload.get("partylist") if isinstance(payload, dict) else payload
    if isinstance(rows, dict):
        rows = [rows] if "nameParty" in rows else list(rows.values())
    if not isinstance(rows, list):
        raise SourceError("Goabase: unbekanntes Antwortformat.")
    warnings, events = [], []
    if len(rows) >= 500:
        warnings.append("Goabase: 500er-Limit erreicht; Auswahl möglicherweise unvollständig.")
    for row in rows:
        try:
            event = parse_party(row)
            # Details enthalten die für Präferenzen benötigten Line-ups und Beschreibung.
            event_id = str(row.get("id", ""))
            if event_id.isdigit():
                try:
                    detail = client.json(f"https://www.goabase.net/api/party/json/{event_id}")
                    if isinstance(detail, dict) and isinstance(detail.get("party"), dict):
                        event = parse_party({**row, **detail["party"]})
                    else:
                        warnings.append("Goabase: Detaildaten fehlen; Matching eingeschränkt.")
                except (SourceError, ValueError, KeyError, TypeError):
                    warnings.append("Goabase: Detailabruf fehlgeschlagen; Matching eingeschränkt.")
            events.append(event)
        except (ValueError, KeyError, TypeError, AttributeError):
            warnings.append("Goabase: ungültigen Datensatz übersprungen.")
    return events, list(dict.fromkeys(warnings))
