"""Öffentliche, redaktionell geprüfte Programmquellen ohne persönliche Daten.

Ein Katalogeintrag ist kein Event. Nur direkte Adapter liefern datierte Events;
allgemeine Programmseiten liefern höchstens lokal geprüfte Namenshinweise.
"""

from .sources.http import safe_url


SOURCES = (
    # Berlin: die ersten vier Quellen haben zusätzlich einen direkten Event-Adapter.
    ("Kater", "Berlin", "Club", "https://www.katerclub.de/", "direkt", False),
    ("Beate Uwe", "Berlin", "Club", "https://beate-uwe.de/", "direkt", False),
    ("Ritter Butzke", "Berlin", "Club", "https://club.ritterbutzke.com/events", "direkt", False),
    ("Gretchen", "Berlin", "Club & Live", "https://www.gretchen-club.de/dates.php", "direkt", False),
    ("Renate", "Berlin", "Club & Live", "https://www.renate.cc/", "recherche", True),
    ("Sisyphos", "Berlin", "Club", "https://www.sisyphos-berlin.net/", "recherche", True),
    ("Club der Visionäre", "Berlin", "Club & Open Air", "https://clubdervisionaere.com/", "recherche", True),
    ("Berghain / Panorama Bar", "Berlin", "Club", "https://www.berghain.berlin/en/", "recherche", True),
    ("Tresor", "Berlin", "Club", "https://tresorberlin.com/", "recherche", False),
    ("Else", "Berlin", "Club & Open Air", "https://www.else.tv/", "recherche", False),
    ("Klunkerkranich", "Berlin", "Club & Live", "https://klunkerkranich.org/", "recherche", True),
    ("Zenner", "Berlin", "Club & Live", "https://zenner.berlin/programm/", "recherche", True),
    ("Holzmarkt 25", "Berlin", "Kulturort", "https://www.holzmarkt.com/kalender/party", "recherche", True),
    ("Fitzroy", "Berlin", "Club", "https://fitzroy-berlin.de/", "recherche", True),
    ("Birgit", "Berlin", "Club & Open Air", "https://www.birgit.club/", "recherche", False),
    ("Heideglühen", "Berlin", "Club", "https://heidegluehen.berlin/monatsvorschau/", "recherche", True),
    ("Panke", "Berlin", "Club & Live", "https://www.pankeculture.com/", "recherche", True),
    ("about blank", "Berlin", "Club", "https://aboutblank.li/", "recherche", False),
    ("ÆDEN", "Berlin", "Club & Open Air", "https://aedenberlin.com/events/", "recherche", True),
    # Andere Zielregionen und der Würzburger 100-km-Ring.
    ("Tanzhaus West", "Frankfurt", "Club", "https://tanzhaus-west.de/programm/", "direkt", False),
    ("Waldschänke Dornheim", "Würzburg", "Club & Open Air", "https://waldschaenke-dornheim.de/club/", "recherche", False),
    ("Airport", "Würzburg", "Club", "https://club-airport.com/", "recherche", False),
    ("Posthalle", "Würzburg", "Club & Live", "https://www.posthalle.de/programm/", "recherche", False),
    ("Die Rakete", "Nürnberg", "Club", "https://dierakete.com/programm/", "recherche", False),
    ("E-Werk Erlangen", "Erlangen", "Club & Live", "https://www.e-werk.de/programm/partys/", "recherche", False),
    ("Grelle Forelle", "Wien", "Club", "https://www.grelleforelle.com/", "recherche", False),
    ("Tanzinsel", "Würzburg", "Festival", "https://tanzinsel.de/", "recherche", False),
    # Festivals sind überregional; die Ausgaben/Line-ups werden jährlich neu geprüft.
    ("Bucht der Träumer", "Helenesee", "Festival", "https://bucht-der-traeumer.de/", "recherche", True),
    ("Fusion", "Lärz", "Festival", "https://fusion-festival.de/de/program", "recherche", True),
    ("Moyn", "Oyten", "Festival", "https://moynfestival.de/", "archiv", False),
)


def catalog():
    return [dict(zip(("name", "city", "kind", "url", "mode", "scan"), row))
            for row in SOURCES if safe_url(row[3])]


def research_pages():
    """Allgemeine Seiten abrufen; Artist-Namen werden erst danach lokal abgeglichen."""
    return [{"name": row["name"], "url": row["url"], "enabled": True}
            for row in catalog() if row["scan"] and row["mode"] == "recherche"]


def merge_research_pages(private_pages):
    """Öffentliche Defaults ergänzen, persönliche Seiten und Abschaltungen behalten."""
    pages = list(private_pages)
    known = {page.get("url") for page in pages if isinstance(page, dict)}
    pages.extend(page for page in research_pages() if page["url"] not in known)
    return pages
