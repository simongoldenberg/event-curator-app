from datetime import datetime
from html import escape
import re
from urllib.parse import quote
from . import APP_VERSION
from .sources.http import safe_url
from .storage import write_private


def md(value):
    value = escape(str(value), quote=False).replace("\n", " ").replace("\r", " ")
    return re.sub(r"([\\`*_{\[\]}()#+.!|>-])", r"\\\1", value)


def write_digest(matches, month, output, warnings, statuses, demo=False):
    output.mkdir(parents=True, exist_ok=True)
    title = f"Event-Digest {month}"
    notice = "FIKTIVE BEISPIELE – keine echten Veranstaltungsempfehlungen." if demo else "Live-/Importdaten: Termine und Tickets vor dem Besuch bei der Quelle prüfen."
    meta = f"Version {APP_VERSION} · erstellt {datetime.now().isoformat(timespec='seconds')}"
    markdown = [f"# {title}", "", notice, "", meta, "", "## Quellenstatus", ""]
    html = ["<!doctype html><html lang='de'><head><meta charset='utf-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1'>",
            "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\">",
            f"<title>{escape(title)}</title><style>body{{max-width:900px;margin:3rem auto;padding:0 1rem;font:17px/1.6 system-ui;background:#f7f5ef;color:#202822}}article{{background:white;padding:1rem;margin:1rem 0;border-left:4px solid #38634d}}a{{color:#24583f}}small{{color:#526057}}</style></head><body>",
            f"<h1>{escape(title)}</h1><p><strong>{escape(notice)}</strong></p><small>{escape(meta)}</small><h2>Quellenstatus</h2><ul>"]
    for status in statuses:
        markdown.append(f"- {md(status)}")
        html.append(f"<li>{escape(status)}</li>")
    html.append("</ul>")
    if warnings:
        markdown += ["", "## Hinweise zur Abdeckung", ""]
        html.append("<h2>Hinweise zur Abdeckung</h2><ul>")
        for warning in dict.fromkeys(warnings):
            markdown.append(f"- {md(warning)}")
            html.append(f"<li>{escape(warning)}</li>")
        html.append("</ul>")
    for category, heading in (("live", "Rubrik 1: Konzerte & Live-Acts"), ("party", "Rubrik 2: Parties, Raves & Open Airs")):
        markdown += ["", f"## {heading}", ""]
        html.append(f"<h2>{escape(heading)}</h2>")
        subset = [match for match in matches if match.event.category == category]
        if not subset:
            message = "Keine passenden regionalen Funde in den erfolgreich ausgewerteten Quellen."
            markdown.append(message)
            html.append(f"<p>{message}</p>")
        for match in subset:
            event = match.event
            details = f"{event.start:%d.%m.%Y %H:%M} (Zeit laut Quelle) · {event.city} · {event.venue or 'Venue nicht angegeben'}"
            relevance = f"Relevanzpunkte: {match.score} · {match.region}: {match.distance}"
            reason = "; ".join(match.reasons)
            markdown += [f"### {md(event.title)}", "", md(details), "", md(relevance), "", md(reason), ""]
            html += [f"<article><h3>{escape(event.title)}</h3><p>{escape(details)}</p><p>{escape(relevance)}</p><p>{escape(reason)}</p>"]
            if safe_url(event.url):
                url = quote(event.url, safe=":/?=&%#@+;,")
                markdown.append(f"[Quelle: {md(event.source)}]({url})")
                html.append(f"<a href='{escape(url, quote=True)}' rel='noreferrer noopener'>Quelle: {escape(event.source)}</a>")
            else:
                markdown.append(f"Quelle: {md(event.source)}")
                html.append(f"<small>Quelle: {escape(event.source)}</small>")
            html.append("</article>")
    markdown += ["", "Relevanzpunkte sind eine nachvollziehbare Heuristik, keine Qualitätsbewertung. Unbekannte Orte werden ausgeschlossen.", ""]
    html.append("<footer>Relevanzpunkte sind eine Heuristik, keine Qualitätsbewertung. Unbekannte Orte werden ausgeschlossen.</footer></body></html>")
    suffix = "-demo" if demo else ""
    base = output / f"digest-{month}{suffix}"
    write_private(base.with_suffix(".md"), "\n".join(markdown))
    write_private(base.with_suffix(".html"), "\n".join(html))
    return base.with_suffix(".md"), base.with_suffix(".html")

