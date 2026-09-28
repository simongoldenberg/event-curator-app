"""Konfigurierte Veranstaltungsseiten: JSON-LD, begrenzte Suche auf derselben Domain."""
from html.parser import HTMLParser
import json
from urllib.parse import urljoin, urlsplit
from ..models import Event
from .http import SourceError, safe_url


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.blocks, self.links, self.buffer = [], [], None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and attrs.get("type", "").lower() == "application/ld+json":
            self.buffer = []
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])

    def handle_data(self, data):
        if self.buffer is not None:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.buffer is not None:
            self.blocks.append("".join(self.buffer))
            self.buffer = None


def walk_events(node):
    if isinstance(node, list):
        for child in node:
            yield from walk_events(child)
    elif isinstance(node, dict):
        types = node.get("@type", [])
        types = [types] if isinstance(types, str) else types
        if any(t in ("Event", "MusicEvent", "DanceEvent", "Festival") for t in types):
            yield node
        else:
            for value in node.values():
                if isinstance(value, (dict, list)):
                    yield from walk_events(value)


def parse_event(node, source, category, page_url):
    location = node.get("location") or {}
    if isinstance(location, list):
        location = location[0] if location else {}
    address = location.get("address") or {}
    geo = location.get("geo") or {}
    if not isinstance(address, dict):
        address = {}
    country = address.get("addressCountry", "")
    if isinstance(country, dict):
        country = country.get("name", "")
    performers = node.get("performer", node.get("performers", []))
    if isinstance(performers, dict):
        performers = [performers]
    if isinstance(performers, list):
        performers = [p.get("name", "") if isinstance(p, dict) else str(p) for p in performers]
    return Event.from_dict({
        "title": node["name"], "start": node["startDate"], "end": node.get("endDate"),
        "city": address.get("addressLocality", ""), "country": country,
        "venue": location.get("name", ""), "latitude": geo.get("latitude"), "longitude": geo.get("longitude"),
        "artists": performers, "tags": node.get("keywords", []), "description": node.get("description", ""),
        "category": category, "url": urljoin(page_url, node.get("url") or page_url),
        "status": node.get("eventStatus", "scheduled"),
    }, source)


def fetch_site(client, settings):
    url, name = settings["url"], settings["name"]
    category = settings.get("category", "party")
    if not safe_url(url) or category not in ("party", "live"):
        raise SourceError("Ungültige Quellenkonfiguration.")
    limit = settings.get("max_pages", 10)
    pattern = settings.get("link_contains", "/events/")
    if not isinstance(limit, int) or not 1 <= limit <= 30 or not isinstance(pattern, str) or not pattern:
        raise SourceError("max_pages muss 1–30 und link_contains ein nichtleerer Text sein.")
    queue, seen, events, warnings = [url], set(), [], []
    while queue and len(seen) < limit:
        current = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)
        try:
            parser = PageParser()
            parser.feed(client.page(current))
            for block in parser.blocks:
                try:
                    for node in walk_events(json.loads(block)):
                        events.append(parse_event(node, name, category, current))
                except (ValueError, KeyError, TypeError, AttributeError):
                    warnings.append(f"{name}: nicht auswertbare strukturierte Eventdaten.")
            if current == url:
                for href in parser.links:
                    target = urljoin(current, href).split("#")[0]
                    if safe_url(target) and urlsplit(target).netloc == urlsplit(url).netloc and pattern in urlsplit(target).path and target not in seen and target not in queue:
                        queue.append(target)
        except SourceError as exc:
            warnings.append(f"{name}: {exc}")
    if queue:
        warnings.append(f"{name}: Seitenlimit erreicht; Auswahl möglicherweise unvollständig.")
    if not events:
        warnings.append(f"{name}: keine auswertbaren Events; Quelle kann blockiert sein oder JavaScript benötigen.")
    return events, list(dict.fromkeys(warnings))
