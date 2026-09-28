from dataclasses import dataclass, field
from datetime import datetime
from math import isfinite
import re
import unicodedata


def normalized(text):
    text = unicodedata.normalize("NFKD", str(text).casefold())
    return " ".join(re.sub(r"[^\w]+", " ", "".join(c for c in text if not unicodedata.combining(c))).split())


def terms(value):
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [v.strip() for v in re.split(r"[;,\n]", str(value or "")) if v.strip()]


def coordinate(value, limit):
    if value is None or value == "":
        return None
    number = float(value)
    if not isfinite(number) or abs(number) > limit:
        raise ValueError("Ungültige Koordinate")
    return number


@dataclass
class Artist:
    name: str
    genres: list[str] = field(default_factory=list)


@dataclass
class Event:
    title: str
    start: datetime
    city: str
    country: str
    venue: str = ""
    category: str = "party"
    artists: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    description: str = ""
    latitude: float | None = None
    longitude: float | None = None
    url: str = ""
    source: str = ""
    status: str = "scheduled"
    end: datetime | None = None

    @classmethod
    def from_dict(cls, row, source="Lokale Datei"):
        title = str(row["title"]).strip()
        if not title or row.get("category", "party") not in ("party", "live"):
            raise ValueError("Titel oder Kategorie ungültig")
        return cls(
            title=title, start=datetime.fromisoformat(row["start"].replace("Z", "+00:00")),
            city=str(row.get("city", "")), country=str(row.get("country", "")).upper(),
            venue=str(row.get("venue", "")), category=row.get("category", "party"),
            artists=terms(row.get("artists")), tags=terms(row.get("tags")),
            description=str(row.get("description", "")),
            latitude=coordinate(row.get("latitude"), 90), longitude=coordinate(row.get("longitude"), 180),
            url=str(row.get("url", "")), source=source, status=str(row.get("status", "scheduled")),
            end=datetime.fromisoformat(row["end"].replace("Z", "+00:00")) if row.get("end") else None,
        )

