"""Spotify-Streaming-Historie lokal zu einer kleinen privaten Künstlerliste verdichten."""
from collections import defaultdict
import csv
from io import StringIO
import json
import os
from pathlib import Path

from .models import normalized


MIN_PLAY_MS = 30_000
MAX_PLAY_MS = 20 * 60_000
MAX_ARTISTS = 200


def import_spotify(folder, destination, replace=False):
    folder, destination = Path(folder), Path(destination)
    if not folder.is_dir():
        raise ValueError("Spotify-Ordner nicht gefunden.")
    files = sorted(folder.glob("Streaming_History_Audio_*.json"))
    if not files:
        raise ValueError("Keine Spotify-Audio-Historie im Ordner gefunden.")
    if destination.exists() and not replace:
        raise FileExistsError("Die lokale Künstlerliste existiert bereits. --replace-import ersetzt sie.")

    streams, seen, latest_year = [], set(), 0
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, list):
            raise ValueError(f"Ungültige Spotify-Datei: {path.name}")
        for row in data:
            if not isinstance(row, dict):
                continue
            artist = row.get("master_metadata_album_artist_name")
            uri = row.get("spotify_track_uri")
            stamp = row.get("ts", "")
            ms = row.get("ms_played")
            if not isinstance(artist, str) or not artist.strip() or not isinstance(uri, str) or not uri.startswith("spotify:track:"):
                continue
            if not isinstance(ms, (int, float)) or not MIN_PLAY_MS <= ms or row.get("skipped") is True:
                continue
            try:
                year = int(stamp[:4])
            except (TypeError, ValueError):
                continue
            if not 2000 <= year <= 2100:
                continue
            identity = (stamp, uri, ms)
            if identity in seen:
                continue
            seen.add(identity)
            streams.append((artist.strip(), year, min(ms, MAX_PLAY_MS)))
            latest_year = max(latest_year, year)
    if not streams:
        raise ValueError("Keine gültigen Musikwiedergaben in der Audio-Historie gefunden.")

    scores = defaultdict(lambda: {"name": "", "minutes": 0.0, "plays": 0, "last_year": 0})
    for name, year, ms in streams:
        record = scores[normalized(name)]
        record["name"] = name
        record["minutes"] += ms / 60_000 * max(0.02, 0.65 ** (latest_year - year))
        record["plays"] += 1
        record["last_year"] = max(record["last_year"], year)
    ranked = sorted(scores.values(), key=lambda row: (-row["minutes"], -row["plays"], normalized(row["name"])))[:MAX_ARTISTS]

    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("artist", "genres", "weighted_hours", "plays", "last_year"))
    for row in ranked:
        writer.writerow((row["name"], "", f"{row['minutes'] / 60:.1f}", row["plays"], row["last_year"]))
    destination.parent.mkdir(parents=True, exist_ok=True)
    # OneDrive blockiert auf manchen Windows-Rechnern das Umbenennen einer temporären CSV.
    # Nur diese lokale Importdatei wird deshalb direkt und mit restriktivem Modus angelegt.
    flags = os.O_WRONLY | os.O_CREAT | (os.O_TRUNC if replace else os.O_EXCL)
    fd = os.open(destination, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
        handle.write(output.getvalue())
    return {"files": len(files), "plays": len(streams), "artists": len(ranked), "destination": destination}
