"""Markdown-Ausgabe und Einbindung der interaktiven HTML-Oberfläche."""
from datetime import datetime
from html import escape
import re
from urllib.parse import quote

from config import DEFAULT_RADIUS_KM
from . import APP_VERSION
from .sources.http import safe_url
from .storage import write_private
from .ui.dashboard import render_dashboard


def md(value):
    value = escape(str(value), quote=False).replace("\n", " ").replace("\r", " ")
    return re.sub(r"([\\`*_{\[\]}()#+.!|>-])", r"\\\1", value)


def write_digest(matches, month, output, warnings, statuses, demo=False, radius_km=DEFAULT_RADIUS_KM, venues=()):
    output.mkdir(parents=True, exist_ok=True)
    notice = "FIKTIVE BEISPIELE – keine echten Veranstaltungsempfehlungen." if demo else "Live-/Importdaten: Termine und Tickets vor dem Besuch bei der Quelle prüfen."
    lines = [f"# Event-Digest {month}", "", notice, "", f"Version {APP_VERSION} · erstellt {datetime.now().isoformat(timespec='seconds')}", "", "## Quellenstatus", ""]
    lines.extend(f"- {md(status)}" for status in statuses)
    if warnings:
        lines += ["", "## Hinweise zur Abdeckung", ""]
        lines.extend(f"- {md(warning)}" for warning in dict.fromkeys(warnings))
    for category, heading in (("live", "Rubrik 1: Konzerte & Live-Acts"), ("party", "Rubrik 2: Parties, Raves & Open Airs")):
        lines += ["", f"## {heading}", ""]
        subset = [match for match in matches if match.scope == "regional" and match.event.category == category]
        if not subset:
            lines.append("Keine passenden regionalen Funde in den erfolgreich ausgewerteten Quellen.")
        for match in subset:
            event = match.event
            details = f"{event.start:%d.%m.%Y %H:%M} (Zeit laut Quelle) · {event.city} · {event.venue or 'Venue nicht angegeben'}"
            relevance = f"Relevanzpunkte: {match.score} · {match.region}: {match.distance}"
            lines += [f"### {md(event.title)}", "", md(details), "", md(relevance), "", md('; '.join(match.reasons)), ""]
            if safe_url(event.url):
                url = quote(event.url, safe=":/?=&%#@+;,")
                lines.append(f"[Quelle: {md(event.source)}]({url})")
            else:
                lines.append(f"Quelle: {md(event.source)}")
    lines += ["", "## Rubrik 3: Reisen · Deutschland, Frankreich, Schweiz & Österreich", ""]
    travel = [match for match in matches if match.scope == "reise"]
    if not travel:
        lines.append("Keine passenden Fernziele in den erfolgreich ausgewerteten Quellen.")
    for match in travel:
        event = match.event
        lines += [f"### {md(event.title)}", "",
                  md(f"{event.start:%d.%m.%Y %H:%M} · {event.city}, {match.region} · {event.venue or 'Venue nicht angegeben'}"), "",
                  md('; '.join(match.reasons)), ""]
        if safe_url(event.url):
            lines.append(f"[Quelle]({quote(event.url, safe=':/?=&%#@+;,')})")
    lines += ["", "## Recherchierte Venues", "",
              "Frühere oder angekündigte Artist-Auftritte sind Hinweise auf passende Programme, keine aktuellen Event-Termine.", ""]
    for venue in venues:
        lines.append(f"- [{md(venue['name'])}]({quote(venue['url'], safe=':/?=&%#@+;,')}) · "
                     f"{md(venue['city'])}, {md(venue['country'])} · "
                     f"{md(', '.join(venue['artists']))} · "
                     f"[Auftrittsbeleg]({quote(venue['evidence_url'], safe=':/?=&%#@+;,')})")
    lines += ["", "Relevanzpunkte sind eine nachvollziehbare Heuristik, keine Qualitätsbewertung. Unbekannte Orte werden ausgeschlossen.", ""]
    suffix = "-demo" if demo else ""
    base = output / f"digest-{month}{suffix}"
    write_private(base.with_suffix(".md"), "\n".join(lines))
    write_private(base.with_suffix(".html"), render_dashboard(matches, month, warnings, statuses, demo, radius_km, venues))
    return base.with_suffix(".md"), base.with_suffix(".html")
