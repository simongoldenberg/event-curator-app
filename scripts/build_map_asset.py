"""Erzeugt eine kleine, offline nutzbare Europakarte aus gemeinfreien Natural-Earth-Daten.

Nur für die Entwicklung ausführen. Die App lädt zur Laufzeit keine Kartendaten nach.
Quelle: https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_admin_0_countries.geojson
Lizenz: Public Domain, https://www.naturalearthdata.com/about/terms-of-use/
"""
import json
from pathlib import Path
from urllib.request import urlopen

SOURCE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
TARGET = Path(__file__).resolve().parents[1] / "event_curator" / "ui" / "europe_map.svg"
COUNTRIES = {"Germany", "Austria", "Switzerland", "France", "Belgium", "Netherlands", "Luxembourg",
             "Czechia", "Czech Republic", "Poland", "Italy", "Slovenia", "Slovakia", "Hungary", "Denmark",
             "United Kingdom", "Spain", "Liechtenstein"}
X_MIN, X_MAX = -5.5, 20.5
Y_MIN, Y_MAX = 42.0, 55.5
WIDTH, HEIGHT = 1200, 740


def project(point):
    lon, lat = point[:2]
    return round((lon - X_MIN) * WIDTH / (X_MAX - X_MIN), 1), round((Y_MAX - lat) * HEIGHT / (Y_MAX - Y_MIN), 1)


def ring_path(ring):
    points = [project(point) for point in ring]
    return "M" + " L".join(f"{x},{y}" for x, y in points) + " Z"


def geometry_path(geometry):
    coordinates = geometry["coordinates"]
    polygons = [coordinates] if geometry["type"] == "Polygon" else coordinates
    return " ".join(ring_path(ring) for polygon in polygons for ring in polygon)


def main():
    with urlopen(SOURCE, timeout=25) as response:
        data = json.load(response)
    paths = []
    for feature in data["features"]:
        name = feature["properties"]["ADMIN"]
        if name in COUNTRIES:
            country = name.replace("&", "&amp;").replace('"', "&quot;")
            paths.append(f'<path class="land" data-country="{country}" d="{geometry_path(feature["geometry"])}"/>')
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(
        f'<svg class="map-base" viewBox="0 0 {WIDTH} {HEIGHT}" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
        + '<rect width="1200" height="740" class="map-water"/>'
        + "".join(paths) + '</svg>\n', encoding="utf-8")
    print(f"Kartenbasis erstellt: {TARGET} ({len(paths)} Länder)")


if __name__ == "__main__":
    main()
