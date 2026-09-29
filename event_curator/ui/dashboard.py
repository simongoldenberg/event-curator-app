"""Selbstständige, responsive HTML-Oberfläche für lokale Monatsberichte."""
from datetime import datetime
from html import escape
import json
import math
from pathlib import Path
from urllib.parse import quote

from config import DEFAULT_RADIUS_KM, REGIONS, radius_for_region
from event_curator import APP_VERSION
from event_curator.featured import FEATURED_ARTISTS
from event_curator.source_catalog import catalog
from event_curator.sources.http import safe_url

ASSETS = Path(__file__).resolve().parent
WEEKDAYS = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")
MAP_X_MIN, MAP_X_MAX = -5.5, 20.5
MAP_Y_MIN, MAP_Y_MAX = 42.0, 55.5


def safe_json(value):
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))


def link(url):
    return escape(quote(url, safe=":/?=&%#@+;,"), quote=True) if safe_url(url) else ""


def region_markers(radius_km):
    content = []
    payload = []
    for name, (lat, lon, _, _) in REGIONS.items():
        local_radius = radius_for_region(name, {"radius_km": radius_km})
        x = (lon - MAP_X_MIN) / (MAP_X_MAX - MAP_X_MIN) * 100
        y = (MAP_Y_MAX - lat) / (MAP_Y_MAX - MAP_Y_MIN) * 100
        diameter_x = 2 * local_radius / (111.2 * math.cos(math.radians(lat))) / (MAP_X_MAX - MAP_X_MIN) * 100
        diameter_y = 2 * local_radius / 111.2 / (MAP_Y_MAX - MAP_Y_MIN) * 100
        content.append(f'<span class="region-ring" style="left:{x:.2f}%;top:{y:.2f}%;width:{diameter_x:.2f}%;height:{diameter_y:.2f}%"></span>')
        content.append(f'<span class="region-dot" style="left:{x:.2f}%;top:{y:.2f}%"></span>')
        content.append(f'<span class="region-label" style="left:{x:.2f}%;top:{y:.2f}%">{escape(name)}</span>')
        payload.append({"name": name, "latitude": lat, "longitude": lon, "radius_km": local_radius})
    return "".join(content), payload


def card(match, index):
    event = match.event
    card_id = f"event-{index}"
    location = " · ".join(part for part in (event.city, event.venue) if part)
    reasons = "; ".join(match.reasons)
    search = " ".join([event.title, event.city, event.venue, match.region, *event.artists, *event.tags])
    actions = []
    if event.latitude is not None and event.longitude is not None:
        actions.append(f'<button type="button" data-map-event="{card_id}" aria-label="{escape(event.title, quote=True)} auf der Karte zeigen">↗ Auf Karte</button>')
    source_url = link(event.url)
    if source_url:
        actions.append(f'<a href="{source_url}" target="_blank" rel="noreferrer noopener">Quelle öffnen ↗</a>')
    else:
        actions.append(f'<span class="event-meta">Quelle: {escape(event.source)}</span>')
    html = (
        f'<article class="event-card" id="{card_id}" data-category="{event.category}" '
        f'data-region="{escape(match.region, quote=True)}" data-scope="{match.scope}" data-search="{escape(search, quote=True)}">'
        f'<div class="event-top"><span class="event-date">{WEEKDAYS[event.start.weekday()]}, {event.start:%d.%m. · %H:%M} Uhr</span>'
        f'<span class="event-score">{match.score} Punkte</span></div>'
        f'<h3>{escape(event.title)}</h3>'
        f'<p class="event-meta">{escape(location or "Ort laut Quelle")}</p>'
        f'<p class="event-meta">{escape(match.region)} · {escape(match.distance)}</p>'
        f'<p class="reason">{escape(reasons)}</p>'
        f'<div class="event-actions">{"".join(actions)}</div></article>'
    )
    data = {"id": card_id, "title": event.title, "city": event.city, "venue": event.venue,
            "region": match.region, "category": event.category, "scope": match.scope,
            "latitude": event.latitude, "longitude": event.longitude}
    return html, data


def event_section(matches, category, heading, subtitle, number, scope="regional"):
    section_id = "reisen" if scope == "reise" else ("live" if category == "live" else "parties")
    selected = [m for m in matches if m.scope == scope and (category == "all" or m.event.category == category)]
    markup = [f'<section class="section event-section" id="{section_id}" data-event-section>',
              '<div class="section-header"><div>',
              f'<span class="section-kicker">Rubrik {number}</span><h2>{heading}</h2></div>',
              f'<p>{subtitle}</p></div>',
              f'<span class="pill"><span data-section-count>{len(selected)}</span>&nbsp;Einträge</span>',
              '<div class="event-grid">']
    events = []
    for index, match in enumerate(matches):
        if match in selected:
            html, item = card(match, index)
            markup.append(html)
            events.append(item)
    markup.extend(['</div><p class="empty section-empty" hidden>In dieser Rubrik passt gerade kein Event zum Filter.</p></section>'])
    return "".join(markup), events


def render_dashboard(matches, month, warnings, statuses, demo=False, radius_km=DEFAULT_RADIUS_KM, venues=()):
    css = (ASSETS / "dashboard.css").read_text(encoding="utf-8")
    script = (ASSETS / "dashboard.js").read_text(encoding="utf-8")
    svg = (ASSETS / "europe_map.svg").read_text(encoding="utf-8")
    rings, regions = region_markers(radius_km)
    live, live_events = event_section(matches, "live", "Konzerte & Live-Acts", "Künstler und Live-Sets mit belegtem Termin in deiner Nähe.", 1)
    parties, party_events = event_section(matches, "party", "Parties, Raves & Open Airs", "Clubnächte, Kollektive und offene Tanzflächen für die nächsten Wochen.", 2)
    travel, travel_events = event_section(matches, "all", "Unterwegs in vier Ländern", "Deutschland, Frankreich, Schweiz und Österreich – passende Termine außerhalb deiner lokalen Suchregionen.", 3, "reise")
    event_data = live_events + party_events + travel_events
    venue_count = len(venues)
    chips = ['<button class="chip" type="button" data-region-filter="all" aria-pressed="true">Alle Orte</button>']
    chips.extend(f'<button class="chip" type="button" data-region-filter="{escape(name, quote=True)}" aria-pressed="false">{escape(name)}</button>' for name in REGIONS)
    chips.extend(f'<button class="chip" type="button" data-region-filter="{name}" aria-pressed="false">{name}</button>'
                 for name in ("Deutschland", "Frankreich", "Schweiz", "Österreich"))
    artist_cards = []
    for number, artist in enumerate(FEATURED_ARTISTS, 1):
        artist_cards.append('<article class="artist-card">'
                            f'<span class="number">0{number}</span><h3>{escape(artist.name)}</h3>'
                            f'<p>{escape(artist.style)} · {escape(artist.note)}</p>'
                            f'<a href="{link(artist.url)}" target="_blank" rel="noreferrer noopener">Musik & Profil ↗</a></article>')
    venue_cards = []
    for venue in venues:
        artists = ", ".join(venue["artists"][:4])
        extra = len(venue["artists"]) - 4
        extra_text = f" + {extra} weitere" if extra > 0 else ""
        artist_detail = (f'<details><summary>Alle {len(venue["artists"])} Artists anzeigen</summary>'
                         f'<p>{escape(", ".join(venue["artists"]))}</p></details>') if extra > 0 else ""
        venue_cards.append(
            '<article class="research-card">'
            f'<div class="research-card-top"><span class="place-city">{escape(venue["city"])} · {escape(venue["country"])}</span>'
            '<span class="verified-mark">Artist-Beleg</span></div>'
            f'<h3>{escape(venue["name"])}</h3>'
            f'<p>Aus deiner Artist-Auswahl: <strong>{escape(artists)}</strong>'
            f'{extra_text}</p>{artist_detail}'
            f'<div class="research-links"><a href="{link(venue["url"])}" target="_blank" rel="noreferrer noopener">Programm ↗</a>'
            f'<a href="{link(venue["evidence_url"])}" target="_blank" rel="noreferrer noopener">Auftrittsbeleg ↗</a></div></article>'
        )
    venue_markup = "".join(venue_cards) if venue_cards else '<p class="empty">Noch keine belegten Venues recherchiert.</p>'
    source_groups = (("Berlin", "Berliner Clubs & Kulturorte", lambda item: item["city"] == "Berlin"),
                     ("regionen", "Weitere Zielregionen", lambda item: item["city"] != "Berlin" and item["kind"] != "Festival"),
                     ("festivals", "Festivals für Reisen", lambda item: item["kind"] == "Festival"))
    source_rows = []
    for key, title, selected in source_groups:
        entries = [item for item in catalog() if selected(item)]
        links = "".join(
            '<li class="catalog-item">'
            f'<span><strong>{escape(item["name"])}</strong><small>{escape(item["city"])} · {escape(item["kind"])}</small></span>'
            f'<span class="catalog-mode">{escape({"direkt": "Termine automatisch", "recherche": "Seitenabgleich" if item["scan"] else "Programm-Link", "archiv": "Archiv / Referenz"}[item["mode"]])}</span>'
            f'<a href="{link(item["url"])}" target="_blank" rel="noreferrer noopener" '
            f'aria-label="Programm von {escape(item["name"], quote=True)} öffnen">Programm ↗</a></li>'
            for item in entries)
        source_rows.append(f'<div class="catalog-group" id="katalog-{key}"><h3>{title} <span>{len(entries)}</span></h3><ul>{links}</ul></div>')
    catalog_markup = "".join(source_rows)
    status_items = "".join(f"<li>{escape(item)}</li>" for item in statuses) or "<li>Keine Quelle abgefragt.</li>"
    warning_items = "".join(f"<li>{escape(item)}</li>" for item in dict.fromkeys(warnings)) or "<li>Keine zusätzlichen Hinweise.</li>"
    demo_message = "Beispielansicht mit erfundenen Events. Die Termine sind nicht buchbar." if demo else "Termine und Tickets vor dem Besuch bei der verlinkten Quelle prüfen."
    demo_badge = "Demo · fiktive Events" if demo else "Lokaler Monatsüberblick"
    focus_text = ("Die Beispiel-Events zeigen die Bedienung und sind frei erfunden." if demo else
                  "Die Live-Auswahl zeigt belegte Downtempo-, Melodic- oder Artist-Treffer aus Clubprogrammen und weiteren Quellen.")
    payload = safe_json({"events": event_data, "regions": regions})
    sections = [
        '<!doctype html><html lang="de"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; style-src \'unsafe-inline\'; script-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">',
        '<meta name="color-scheme" content="light">',
        f'<title>Event Curator · {escape(month)}</title><style>{css}</style></head><body>',
        '<a class="sr-only" href="#inhalt">Zum Inhalt springen</a>',
        '<header class="masthead"><div class="wrap"><div class="topline"><a class="brand" href="#start">◌ EVENT CURATOR</a>',
        f'<span class="edition">Ausgabe {escape(month)} · Version {APP_VERSION}</span></div>',
        '<div class="hero" id="start"><span class="eyebrow">Dein Kompass für lange Nächte</span>',
        '<h1>Finde deinen<br><em>nächsten Sound.</em></h1>',
        f'<p>Downtempo, Organic und Melodic im Fokus. Würzburg mit {max(100, radius_km):g} km Umkreis, vier weitere Städte mit {radius_km:g} km – '
        'und ein eigener Blick auf Deutschland, Frankreich, die Schweiz und Österreich.</p>',
        '<div class="hero-actions"><a class="button button-primary" href="#karte">↗ Karte entdecken</a>',
        '<a class="button button-ghost" href="#live">Konzerte ansehen</a>',
        '<a class="button button-ghost" href="#reisen">Reisen ansehen</a></div></div></div></header>',
        '<nav class="quicknav" aria-label="Seitenbereiche"><div class="wrap">',
        '<a href="#ueberblick">Überblick</a><a href="#karte">Karte</a><a href="#live">Konzerte</a>',
        '<a href="#parties">Parties</a><a href="#reisen">Vier Länder</a><a href="#katalog">Clubs & Festivals</a><a href="#venues">Artist-Venues</a>',
        '<a href="#artists">Downtempo-Radar</a><a href="#quellen">Quellen</a>',
        '</div></nav><main id="inhalt" class="wrap">',
        '<section class="intro" id="ueberblick"><div class="intro-grid"><div>',
        f'<span class="section-kicker">{escape(demo_badge)}</span><h2>Alles auf einen Blick.</h2>',
        f'<p>{escape(focus_text)} Die Punkte erklären die Übereinstimmung; sie bewerten keine Veranstaltung.</p>',
        '</div><aside class="notice"><strong>Gut zu wissen</strong>',
        f'{escape(demo_message)}<br>Uhrzeiten stehen so im jeweiligen Quelleneintrag.</aside></div>',
        '<div class="summary">',
        f'<div class="stat"><strong>{len(matches)}</strong><span>Events im Monat</span></div>',
        f'<div class="stat"><strong>{venue_count}</strong><span>Venues mit Artist-Beleg</span></div>',
        f'<div class="stat"><strong>{len(REGIONS)} + 4</strong><span>Städte + Reiseländer</span></div>',
        '</div></section>',
        '<section class="section" id="karte"><div class="section-header"><div>',
        '<span class="section-kicker">01 / Entdecken</span><h2>Wo passiert etwas?</h2></div>',
        '<p>Wähle eine Stadt oder ein Reiseland. Pins zeigen nur Events mit Koordinaten; alle belegten Clubs stehen weiter unten.</p></div>',
        '<div class="filters"><div>',
        '<div class="filter-group" aria-label="Region wählen">', "".join(chips), '</div>',
        '<div class="filter-group" style="margin-top:9px" aria-label="Eventart wählen">',
        '<button class="chip" type="button" data-category-filter="all" aria-pressed="true">Alles</button>',
        '<button class="chip" type="button" data-category-filter="live" aria-pressed="false">Konzerte</button>',
        '<button class="chip" type="button" data-category-filter="party" aria-pressed="false">Parties & Open Airs</button></div></div>',
        '<div><label class="sr-only" for="event-search">Events suchen</label>',
        '<input class="search" id="event-search" type="search" placeholder="Artist, Ort oder Event suchen" autocomplete="off">',
        '<span class="sr-only" id="result-count" aria-live="polite"></span></div></div>',
        '<div class="map-layout"><div><div class="map-frame" id="map-frame" aria-label="Interaktive Karte der Veranstaltungsorte">',
        f'<div class="map-world" id="map-world">{svg}{rings}<div id="map-pins"></div></div>',
        '<div class="map-controls"><button type="button" id="zoom-in" aria-label="Karte vergrößern">+</button>',
        '<button type="button" id="zoom-out" aria-label="Karte verkleinern">−</button>',
        '<button type="button" id="zoom-reset" aria-label="Kartenausschnitt zurücksetzen">Alle</button></div>',
        '<div class="map-popup" id="map-popup" hidden><button class="popup-close" id="popup-close" type="button" aria-label="Infokarte schließen">×</button>',
        '<strong></strong><p></p><button type="button" data-open-event>Event ansehen ↗</button></div></div>',
        '<p class="map-note">Kartenbasis: Natural Earth, gemeinfrei. Pins mit ungenauem oder unbekanntem Venue-Namen zeigen die Event-Koordinate; maßgeblich ist der Quellenlink.</p></div>',
        '<aside class="venue-panel"><div class="venue-panel-head"><strong>Orte in deiner Auswahl</strong>',
        '<p><span id="venue-count">0</span> Pins · Zum Zentrieren antippen</p></div>',
        '<div class="venue-list" id="venue-list"></div></aside></div>',
        '<p class="empty" id="no-results" hidden>Keine Events für diese Auswahl. Probiere einen anderen Ort, Typ oder Suchbegriff.</p></section>',
        live, parties, travel,
        '<section class="section" id="katalog"><div class="section-header"><div>',
        '<h2>Clubs & Festivals im Blick.</h2></div>',
        '<p>Offizielle Programme für die weitere Suche. Nur „Termine automatisch“ liefert direkt datierte Eventkarten. „Seitenabgleich“ prüft Artist-Namen lokal und liefert erst einmal Hinweise.</p></div>',
        '<p class="catalog-note">Fusion und Bucht liegen außerhalb des Berliner 50-km-Rings. Moyn bleibt nach der Abschiedsausgabe 2026 als Referenz sichtbar.</p>',
        f'<div class="catalog-groups">{catalog_markup}</div></section>',
        '<section class="section" id="venues"><div class="section-header"><div>',
        '<span class="section-kicker">Venue-Scout</span><h2>Orte, die deinen Sound kennen.</h2></div>',
        '<p>Frühere oder angekündigte Gigs aus deiner lokalen Artist-Auswahl. Folge dem Programm-Link für neue Termine; ein Auftrittsbeleg ist noch kein künftiges Event.</p></div>',
        f'<div class="research-grid">{venue_markup}</div></section>',
        '<section class="section" id="artists"><div class="section-header"><div>',
        '<span class="section-kicker">Artist-Radar</span><h2>Langsamer. Tiefer. Wärmer.</h2></div>',
        '<p>Öffentliche Künstlerprofile für Downtempo und Organic Sounds. Sie sind keine bestätigten Auftritte und keine persönlichen Favoriten.</p></div>',
        f'<div class="artist-grid">{"".join(artist_cards)}</div></section>',
        '<section class="section" id="quellen"><div class="section-header"><div>',
        '<span class="section-kicker">Transparenz</span><h2>Woher kommen die Funde?</h2></div>',
        '<p>Fehler und Lücken bleiben sichtbar, damit du einen leeren Bericht richtig einordnen kannst.</p></div>',
        '<div class="sources"><div class="source-box"><h3>Abgefragte Quellen</h3><ul>', status_items, '</ul></div>',
        '<div class="source-box"><h3>Hinweise</h3><ul>', warning_items, '</ul></div></div></section>',
        '</main><footer class="footer"><div class="wrap"><span>Event Curator · lokal erstellt · persönliche Daten bleiben außerhalb von Git</span>',
        f'<span>Erstellt {datetime.now():%d.%m.%Y %H:%M} · Würzburg {max(100, radius_km):g} km · sonst {radius_km:g} km</span></div></footer>',
        f'<script id="dashboard-data" type="application/json">{payload}</script><script>{script}</script></body></html>',
    ]
    return "".join(sections)
