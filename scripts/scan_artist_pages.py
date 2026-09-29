"""Gleicht private Artist-Namen lokal mit allgemein abgerufenen Clubseiten ab."""
import argparse
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import DATA, EXPORTS, SOURCES  # noqa: E402
from event_curator.featured import FEATURED_ARTISTS  # noqa: E402
from event_curator.models import normalized  # noqa: E402
from event_curator.sources.http import HttpClient, SourceError, safe_url  # noqa: E402
from event_curator.storage import read_artists, read_json, write_private  # noqa: E402
from event_curator.source_catalog import merge_research_pages  # noqa: E402


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def name_hits(html, artists):
    parser = VisibleText()
    parser.feed(html)
    text = " " + normalized(" ".join(parser.parts)) + " "
    return [artist.name for artist in artists
            if len(normalized(artist.name).replace(" ", "")) >= 4
            and " " + normalized(artist.name) + " " in text]


def scan(client, pages, artists):
    results = []
    for page in pages:
        if not page.get("enabled", True) or not safe_url(page.get("url", "")):
            continue
        try:
            hits = name_hits(client.page(page["url"]), artists)
            results.append((page["name"], page["url"], hits, ""))
        except (SourceError, ValueError, KeyError) as exc:
            results.append((page.get("name", "Unbekannte Seite"), page["url"], [], str(exc)))
    return results


def main():
    parser = argparse.ArgumentParser(description="Privater Namensabgleich mit allgemeinen Clubseiten")
    parser.add_argument("--month", default=date.today().strftime("%Y-%m"))
    args = parser.parse_args()
    datetime.strptime(args.month, "%Y-%m")
    artist_file = next((p for p in (DATA / "artists.csv", DATA / "user_artists.csv") if p.exists()), None)
    if artist_file is None:
        print("Keine private Artist-Liste; Seitenabgleich übersprungen.")
        return 0
    artists = read_artists(artist_file)
    settings = read_json(SOURCES, {})
    if not isinstance(settings, dict) or not isinstance(settings.get("research_pages", []), list):
        raise ValueError("Ungültige Quellenkonfiguration.")
    results = scan(HttpClient(), merge_research_pages(settings.get("research_pages", [])),
                   artists + list(FEATURED_ARTISTS))
    private_names = {normalized(artist.name) for artist in artists}
    lines = [f"# Clubseiten-Abgleich {args.month}", "",
             f"{len(artists)} private Artists und {len(FEATURED_ARTISTS)} öffentliche Stilvorschläge lokal geprüft.",
             "Es wurden nur allgemeine Clubseiten abgerufen; Artist-Namen wurden nicht in Anfragen übertragen.",
             "Namensnennungen sind keine bestätigten Auftritte. Datum, Ort und Line-up einzeln prüfen.", ""]
    for name, url, hits, error in results:
        lines.extend([f"## {name}", "", url, ""])
        if error:
            lines.append(f"Hinweis: {error}")
        elif hits:
            personal = [hit for hit in hits if normalized(hit) in private_names]
            suggested = [hit for hit in hits if normalized(hit) not in private_names]
            if personal:
                lines.append("Aus deiner Liste: " + ", ".join(personal))
            if suggested:
                lines.append("Öffentliche Stilvorschläge: " + ", ".join(suggested))
        else:
            lines.append("Keine Namenshinweise.")
        lines.append("")
    EXPORTS.mkdir(parents=True, exist_ok=True)
    output = EXPORTS / f"artist-scan-{args.month}.md"
    write_private(output, "\n".join(lines))
    print(f"{len(results)} Clubseiten, {sum(len(item[2]) for item in results)} Namenshinweise: {output}")
    return 2 if any(item[3] for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
