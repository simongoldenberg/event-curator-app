"""Belegbasierte Künstler-/Venue-Vorschläge und unbestätigte Gig-Hinweise."""
from datetime import date
from html.parser import HTMLParser
import json
import re
from urllib.parse import urljoin, urlsplit
from .matching import contains
from .models import normalized
from .sources.http import SourceError, safe_url
from .storage import write_json, write_private
from .reports import md


class HintParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text, self.links, self.descriptions, self.scripts = [], [], [], []
        self.hidden = 0
        self.script = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("script", "style"):
            self.hidden += 1
            if tag == "script":
                self.script = []
        if tag == "meta" and attrs.get("name", attrs.get("property", "")) in ("description", "og:description"):
            self.descriptions.append(attrs.get("content", ""))
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden = max(0, self.hidden - 1)
            if tag == "script" and self.script is not None:
                self.scripts.append("".join(self.script))
                self.script = None

    def handle_data(self, data):
        if self.script is not None:
            self.script.append(data)
        if not self.hidden and data.strip():
            self.text.append(data.strip())


def descriptions(node):
    if isinstance(node, list):
        for item in node:
            yield from descriptions(item)
    elif isinstance(node, dict):
        for key, value in node.items():
            if key in ("description", "bio") and isinstance(value, str):
                yield value
            elif isinstance(value, (dict, list)):
                yield from descriptions(value)


def page_hints(client, settings):
    parser = HintParser()
    url = settings["url"]
    parser.feed(client.page(url))
    chunks = parser.descriptions[:]
    # SoundCloud kann Profilbeschreibungen als öffentliche Hydration-Daten ausliefern.
    if urlsplit(url).hostname in ("soundcloud.com", "www.soundcloud.com"):
        for script in parser.scripts:
            text = script.strip()
            if text.startswith("window.__sc_hydration ="):
                try:
                    chunks.extend(descriptions(json.loads(text.partition("=")[2].strip().rstrip(";"))))
                except ValueError:
                    pass
    chunks.extend(parser.text)
    hints = []
    for chunk in chunks:
        for line in chunk.splitlines():
            if re.search(r"\b(gigs?|tour|dates?|upcoming|line.?up|residents?|festival|club|live|open.?air)\b|\d{1,2}[./]\d{1,2}", line, re.I):
                hints.append(line[:700])
    links = []
    for href in parser.links:
        target = urljoin(url, href)
        if safe_url(target) and target not in links:
            links.append(target)
    candidates = []
    section_start = settings.get("artist_section_start")
    if section_start:
        active = False
        for line in parser.text:
            if normalized(line) == normalized(section_start):
                active = True
                continue
            if active and normalized(line) == normalized(settings.get("artist_section_end", "")):
                break
            if active and 1 < len(line) < 100 and normalized(line) not in ("image", "tickets", "more", "read more"):
                candidates.append(line)
    return {"name": settings["name"], "url": url, "artist": settings.get("artist", ""),
            "status": "unbestätigte Recherchehinweise", "hints": list(dict.fromkeys(hints))[:40],
            "links": links[:60], "artist_candidates": list(dict.fromkeys(candidates))[:100]}


def venue_network(events, artists):
    favorites = {normalized(artist.name) for artist in artists}
    past_venues, recommendations = {}, {}
    for event in events:
        if event.start.date() >= date.today():
            continue
        matched = [artist.name for artist in artists if any(normalized(artist.name) == normalized(a) for a in event.artists) or contains(event.description + " " + event.title, artist.name)]
        if matched and event.venue:
            key = (normalized(event.venue), normalized(event.city))
            past_venues[key] = {"venue": event.venue, "city": event.city, "favorite_artists": matched,
                                "date": event.start.date().isoformat(), "evidence": event.url}
    for event in events:
        key = (normalized(event.venue), normalized(event.city))
        if key not in past_venues:
            continue
        for artist in event.artists:
            if normalized(artist) not in favorites:
                recommendations.setdefault(normalized(artist), {"artist": artist, "venue": event.venue,
                    "reason": "Gleiche Venue wie ein früherer Auftritt eines Favoriten; musikalische Nähe ungeprüft.", "evidence": event.url})
    return list(past_venues.values()), list(recommendations.values())


def write_discovery(events, artists, pages, data_dir, exports, warnings):
    venues, recommendations = venue_network(events, artists)
    payload = {"checked_on": date.today().isoformat(), "venues": venues, "artist_suggestions": recommendations, "page_hints": pages, "warnings": warnings}
    write_json(data_dir / "user_discovery.json", payload)
    lines = ["# Künstler- und Club-Recherche", "", "Recherchehinweise sind keine bestätigten Events und keine automatisch übernommenen Favoriten.", "", "## Frühere Auftritte und verbundene Venues", ""]
    for venue in venues:
        lines.append(f"- {md(venue['venue'])}, {md(venue['city'])}: {md(', '.join(venue['favorite_artists']))} ({venue['date']}) – {md(venue['evidence'])}")
    if not venues:
        lines.append("Noch keine belegten früheren Auftritte der Favoriten in den geladenen Daten.")
    lines += ["", "## Weitere Artists aus denselben Venues", ""]
    for item in recommendations:
        lines.append(f"- {md(item['artist'])} – {md(item['venue'])}; {md(item['reason'])} Quelle: {md(item['evidence'])}")
    for page in pages:
        lines += ["", f"## {md(page['name'])}", "", md(page['url']), ""]
        lines += [f"- {md(hint)}" for hint in page["hints"]] or ["Keine Gig-Hinweise im auswertbaren HTML gefunden."]
        if page.get("artist_candidates"):
            lines += ["", "### Artist-Vorschläge aus der konfigurierten Programm-/Resident-Sektion", "",
                      "Namen aus der Quelle; musikalische Nähe und Schreibweise noch prüfen.", ""]
            lines += [f"- {md(artist)}" for artist in page["artist_candidates"]]
        lines += ["", "### Weiterführende Links zur Prüfung", ""]
        lines += [f"- {md(link)}" for link in page["links"]]
    lines += ["", "## Quellenhinweise", "", *[f"- {md(w)}" for w in dict.fromkeys(warnings)], ""]
    write_private(exports / "discovery.md", "\n".join(lines))
    return exports / "discovery.md"
