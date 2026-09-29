"""Öffentliche Programmseiten ausgewählter Clubs ohne externe Bibliotheken lesen."""
from datetime import datetime
from html.parser import HTMLParser
import re
from urllib.parse import urljoin

from ..models import Event
from .http import SourceError, safe_url


CLUBS = (
    {"name": "Kater", "url": "https://www.katerclub.de/", "city": "Berlin", "country": "DE",
     "latitude": 52.511915, "longitude": 13.425409, "parser": "kater"},
    {"name": "Beate Uwe", "url": "https://beate-uwe.de/", "city": "Berlin", "country": "DE",
     "latitude": 52.51748, "longitude": 13.41902, "parser": "beate"},
    {"name": "Tanzhaus West", "url": "https://tanzhaus-west.de/programm/", "city": "Frankfurt", "country": "DE",
     "latitude": 50.09803, "longitude": 8.6464, "parser": "tanzhaus"},
    {"name": "Ritter Butzke", "url": "https://club.ritterbutzke.com/events", "city": "Berlin", "country": "DE",
     "latitude": None, "longitude": None, "parser": "ritter"},
    {"name": "Gretchen", "url": "https://www.gretchen-club.de/dates.php", "city": "Berlin", "country": "DE",
     "latitude": 52.4975, "longitude": 13.3903, "parser": "gretchen"},
)

MONTHS = {name: number for number, name in enumerate(
    ("januar", "februar", "märz", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "dezember"), 1)}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class Node:
    def __init__(self, tag="", attrs=(), parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children = []

    def nodes(self, predicate):
        for child in self.children:
            if isinstance(child, Node):
                if predicate(child):
                    yield child
                yield from child.nodes(predicate)

    def text(self):
        if self.tag in ("script", "style"):
            return ""
        return " ".join(part.text() if isinstance(part, Node) else part for part in self.children).strip()

    def has_class(self, word):
        return word in self.attrs.get("class", "").split()

    def first(self, predicate):
        return next(self.nodes(predicate), None)


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, attrs, self.stack[-1]))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        if self.stack[-1].tag not in ("script", "style"):
            self.stack[-1].children.append(data)


def document(html):
    parser = Tree()
    parser.feed(html)
    return parser.root


def clean(node):
    return re.sub(r"\s+", " ", node.text()).strip() if node else ""


def make_event(club, title, start, url, description="", tags=(), venue=None, category="party"):
    return Event.from_dict({"title": title, "start": start.isoformat(), "city": club["city"],
                            "country": club["country"], "venue": venue or club["name"],
                            "latitude": club["latitude"], "longitude": club["longitude"],
                            "category": category, "description": description[:4000], "tags": list(tags),
                            "url": url}, club["name"])


def kater_events(root, club, year, month):
    events = []
    for article in root.nodes(lambda n: n.tag == "article" and n.has_class("event")):
        title = clean(article.first(lambda n: n.has_class("date-title")))
        summary = article.first(lambda n: n.has_class("entry-summary"))
        description = clean(summary)
        stamp = re.search(r"\b(\d{1,2})\.(\d{1,2})\s+(\d{1,2}):(\d{2})\b", description)
        if not title or not stamp or int(stamp[2]) != month:
            continue
        try:
            start = datetime(year, month, int(stamp[1]), int(stamp[3]), int(stamp[4]))
        except ValueError:
            continue
        anchor = article.attrs.get("id", "")
        url = club["url"] + ("#" + anchor if re.fullmatch(r"event-\d+", anchor) else "")
        tags = ["Open Air"] if "open air" in description.casefold() or "open air" in title.casefold() else []
        events.append(make_event(club, title, start, url, description, tags))
    return events


def beate_events(root, club, year, month):
    events = []
    date_pattern = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b")
    nodes = list(root.nodes(lambda n: True))
    positions = [index for index, node in enumerate(nodes)
                 if node.has_class("elementor-icon-list-text") and date_pattern.search(clean(node))]
    for position, next_position in zip(positions, positions[1:] + [len(nodes)]):
        stamp_node = nodes[position]
        match = date_pattern.search(clean(stamp_node))
        day, listed_month, listed_year = map(int, match.groups())
        listed_year += 2000 if listed_year < 100 else 0
        if (listed_year, listed_month) != (year, month):
            continue
        chunk = nodes[position + 1:next_position]
        paragraphs = [n for n in chunk if n.tag == "p" and clean(n)]
        times = [clean(n) for n in chunk if n.has_class("elementor-icon-list-text")]
        clock = next((match for t in times if (match := re.fullmatch(r"(\d{1,2}):(\d{2})", t))), None)
        if clock is None:
            continue
        title = clean(paragraphs[0])
        if not title:
            continue
        try:
            start = datetime(year, month, day, int(clock[1]), int(clock[2]))
        except ValueError:
            continue
        link = paragraphs[0].first(lambda n: n.tag == "a" and safe_url(n.attrs.get("href", "")))
        url = link.attrs["href"] if link else club["url"]
        description = " ".join(clean(p) for p in paragraphs[1:4])
        tags = ["Downtempo"] if "beate barfuss" in title.casefold() else []
        events.append(make_event(club, title, start, url, description, tags))
    return events


def tanzhaus_events(client, root, club, year, month):
    events, warnings = [], []
    current_month = None
    rows = root.nodes(lambda n: n.has_class("cm_thw_events_list"))
    for row in rows:
        if not row.has_class("event"):
            headings = [clean(n).casefold() for n in row.nodes(lambda n: n.tag == "h1")]
            current_month = next((MONTHS[heading] for heading in headings if heading in MONTHS), current_month)
            continue
        if current_month != month:
            continue
        left = row.first(lambda n: n.has_class("content-left"))
        right = row.first(lambda n: n.has_class("content-right"))
        day_match = re.search(r"/(\d{1,2})", clean(left))
        title = clean(right.first(lambda n: n.tag == "h2")) if right else ""
        link = right.first(lambda n: n.tag == "a" and bool(n.attrs.get("href"))) if right else None
        if not day_match or not title or not link:
            continue
        url = urljoin(club["url"], link.attrs["href"])
        if not safe_url(url) or not url.startswith("https://tanzhaus-west.de/veranstaltungen/"):
            continue
        try:
            detail = document(client.page(url))
            body = detail.first(lambda n: n.has_class("event_detail"))
            content = clean(body)
            clock = re.search(r"\bAb\s+(\d{1,2})(?::(\d{2}))?\s*Uhr\b", content, re.I)
            if not clock:
                warnings.append(f"Tanzhaus West: Uhrzeit für {title} fehlt; Event ausgelassen.")
                continue
            start = datetime(year, month, int(day_match[1]), int(clock[1]), int(clock[2] or 0))
        except SourceError as exc:
            warnings.append(f"Tanzhaus West: Detailseite für {title} nicht erreichbar ({exc}).")
            continue
        except ValueError:
            warnings.append(f"Tanzhaus West: ungültiges Datum für {title}.")
            continue
        genre = clean(right.first(lambda n: n.tag == "p"))
        events.append(make_event(club, title, start, url, (genre + " " + content)[:4000], [genre] if genre else []))
    return events, warnings


def ritter_events(client, root, club, year, month):
    events, warnings = [], []
    for anchor in root.nodes(lambda n: n.tag == "a" and n.has_class("event-link")):
        teaser = clean(anchor.parent)
        stamp = re.search(r"\b(\d{1,2})\.(\d{1,2})\.(\d{2})\b", teaser)
        if not stamp or (int(stamp[2]), 2000 + int(stamp[3])) != (month, year):
            continue
        url = urljoin(club["url"], anchor.attrs.get("href", ""))
        if not safe_url(url) or not url.startswith("https://club.ritterbutzke.com/event/"):
            continue
        try:
            detail = document(client.page(url))
            title = clean(detail.first(lambda n: n.tag == "h1"))
            content = clean(detail).split("For fans of:", 1)[0]
            clock = re.search(r"\bab\s+(\d{1,2}):(\d{2})\b", content, re.I)
            if not title or not clock:
                warnings.append("Ritter Butzke: Titel oder Uhrzeit auf Detailseite fehlt; Event ausgelassen.")
                continue
            start = datetime(year, month, int(stamp[1]), int(clock[1]), int(clock[2]))
            events.append(make_event(club, title, start, url, content))
        except (SourceError, ValueError):
            warnings.append("Ritter Butzke: Detailseite nicht auswertbar; Event ausgelassen.")
    return events, warnings


def gretchen_events(root, club, year, month):
    """Liest datierte Live-Shows und Clubnächte aus dem offiziellen Gretchen-Programm."""
    events = []
    for gig in root.nodes(lambda n: n.has_class("gig")):
        date_text = clean(gig.first(lambda n: n.has_class("date")))
        stamp = re.search(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b", date_text)
        if not stamp or (int(stamp[2]), int(stamp[3])) != (month, year):
            continue
        clock = re.search(r"\bShow:\s*(\d{1,2})[.:](\d{2})\b", date_text)
        if clock is None:
            clock = re.search(r"\bDoors:\s*(\d{1,2})[.:](\d{2})\b", date_text)
        heading = gig.first(lambda n: n.tag == "h2")
        title = clean(heading)
        anchor = heading.first(lambda n: n.tag == "a") if heading else None
        if not clock or not title or anchor is None:
            continue
        url = urljoin(club["url"], anchor.attrs.get("href", ""))
        if not safe_url(url) or not url.startswith("https://www.gretchen-club.de/detail.php?id="):
            continue
        lineup = clean(gig.first(lambda n: n.has_class("lineup")))
        title_section = gig.first(lambda n: n.has_class("title"))
        genres = " ".join(part.strip() for part in title_section.children if isinstance(part, str)).strip() if title_section else ""
        try:
            start = datetime(year, month, int(stamp[1]), int(clock[1]), int(clock[2]))
        except ValueError:
            continue
        category = "live" if re.search(r"\*live\*", lineup, re.I) else "party"
        events.append(make_event(club, title, start, url, lineup, [genres] if genres else [], category=category))
    return events


def fetch_club(client, club, month):
    """Liest echte Terminangaben einer bekannten Primärquelle; keine Genre-Vermutung aus dem Clubnamen."""
    if club not in CLUBS:
        raise SourceError("Unbekannte Clubquelle.")
    year, number = map(int, month.split("-"))
    root = document(client.page(club["url"]))
    if club["parser"] == "kater":
        events, warnings = kater_events(root, club, year, number), []
    elif club["parser"] == "beate":
        events, warnings = beate_events(root, club, year, number), []
    elif club["parser"] == "ritter":
        events, warnings = ritter_events(client, root, club, year, number)
    elif club["parser"] == "gretchen":
        events, warnings = gretchen_events(root, club, year, number), []
    else:
        events, warnings = tanzhaus_events(client, root, club, year, number)
    if not events:
        warnings.append(f"{club['name']}: keine auswertbaren Events für {month}; Programm kann fehlen oder sich geändert haben.")
    return events, warnings
