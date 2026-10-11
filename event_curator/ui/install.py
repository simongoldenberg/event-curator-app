"""Kleine lokale PWA-Dateien ohne externe Bibliotheken erzeugen."""
import json
import struct
import zlib


def manifest():
    return json.dumps({
        "name": "Event Curator",
        "short_name": "Events",
        "description": "Dein privater Monatsbericht für Konzerte und elektronische Events.",
        "id": "./app.html",
        "start_url": "./app.html",
        "scope": "./",
        "display": "standalone",
        "background_color": "#f7f7f2",
        "theme_color": "#153b35",
        "icons": [
            {"src": "./event-curator-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "./event-curator-512.png", "sizes": "512x512", "type": "image/png"},
        ],
    }, ensure_ascii=False, separators=(",", ":"))


def icon_png(size):
    """Ein schlichtes Kompass-Symbol als PNG, rein mit Standardbibliothek."""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)

    rows = []
    center = (size - 1) / 2
    for y in range(size):
        row = bytearray(b"\x00")
        for x in range(size):
            dx, dy = x - center, y - center
            radius = (dx * dx + dy * dy) ** 0.5
            if radius < size * .245:
                color = (223, 240, 173)
            elif radius < size * .31:
                color = (70, 116, 91)
            else:
                color = (21, 59, 53)
            if abs(dx) < size * .035 and -size * .22 < dy < size * .07:
                color = (214, 109, 77)
            row.extend(color)
        rows.append(bytes(row))
    raw = b"".join(rows)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">2I5B", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))
