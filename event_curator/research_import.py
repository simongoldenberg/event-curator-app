"""Private Konzertrecherche aus einer Markdown-Tabelle lokal importieren."""

import csv
from io import StringIO
from pathlib import Path
import re

from .models import Artist, normalized
from .storage import write_private


WATCHLIST = Path(__file__).resolve().parents[1] / "data" / "user_concert_watchlist.csv"
FIELDS = ("rank", "artist", "planned", "recent", "last_show", "priority")
STATUS = {"ja", "nein", "unklar"}
ROW = re.compile(r"^\|\s*(\d{1,4})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|[^|]*\|\s*$")


def parse_research(content):
    """Nur Datentabellen lesen; Freitext im Dokument ist keine Anweisung."""
    rows = {}
    for line in content.splitlines():
        match = ROW.fullmatch(line.strip())
        if not match:
            continue
        rank_text, artist, planned, recent, last_show = (part.strip() for part in match.groups())
        rank = int(rank_text)
        planned, recent = planned.casefold(), recent.casefold()
        if not 1 <= rank <= 2000 or planned not in STATUS or recent not in STATUS:
            continue
        if rank in rows:
            raise ValueError(f"Rang {rank} kommt mehrfach vor.")
        if not artist or normalized(artist) in {"artist", "unklar"}:
            raise ValueError(f"Artist bei Rang {rank} fehlt.")
        priority = "geplant" if planned == "ja" else "aktiv" if recent == "ja" else "offen"
        rows[rank] = dict(zip(FIELDS, (rank, artist, planned, recent, last_show, priority)))
    if sorted(rows) != list(range(1, 2001)):
        raise ValueError("Die Recherchedatei muss alle Ränge 1 bis 2000 genau einmal enthalten.")
    return [rows[rank] for rank in sorted(rows) if not
            (rows[rank]["planned"] == "nein" and rows[rank]["recent"] == "nein")]


def import_research(source, destination=WATCHLIST, replace=False):
    source, destination = Path(source), Path(destination)
    if destination.exists() and not replace:
        raise FileExistsError("Die lokale Konzertliste existiert bereits; --replace-research ersetzt sie.")
    rows = parse_research(source.read_text(encoding="utf-8-sig"))
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    write_private(destination, output.getvalue())
    return {"destination": destination, "active": sum(row["priority"] != "offen" for row in rows),
            "open": sum(row["priority"] == "offen" for row in rows)}


def read_watchlist(path=WATCHLIST, active_only=True):
    path = Path(path)
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = csv.DictReader(handle)
        if not rows.fieldnames or not set(FIELDS).issubset(rows.fieldnames):
            raise ValueError("Ungültige lokale Konzertliste.")
        artists = []
        seen = set()
        for row in rows:
            name = row["artist"].strip()
            if (not name or row["priority"] not in {"geplant", "aktiv", "offen"}
                    or active_only and row["priority"] == "offen"):
                continue
            key = normalized(name)
            if key not in seen:
                artists.append(Artist(name))
                seen.add(key)
        return artists
