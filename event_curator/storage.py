import csv
import json
import os
import tempfile
from pathlib import Path
from .models import Artist, normalized, terms


def read_json(path, default=None):
    return json.loads(Path(path).read_text(encoding="utf-8-sig")) if Path(path).exists() else default


def write_private(path, text):
    """Atomarer Austausch; unter Unix neue Dateien nur für den Besitzer lesbar."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="user_tmp_", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path, value):
    write_private(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def read_artists(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        rows = csv.DictReader(handle, dialect=dialect)
        if not rows.fieldnames or "artist" not in rows.fieldnames:
            raise ValueError("Künstler-CSV benötigt die Spalte 'artist' (optional: 'genres').")
        artists = {}
        for row in rows:
            name = (row.get("artist") or "").strip()
            if name:
                artists[normalized(name)] = Artist(name, terms(row.get("genres")))
        return list(artists.values())

