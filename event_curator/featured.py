"""Öffentlich belegte Genre-Entdeckungen; keine persönlichen Favoriten und keine Gig-Zusagen."""
from dataclasses import dataclass


@dataclass(frozen=True)
class FeaturedArtist:
    name: str
    style: str
    note: str
    url: str


FEATURED_ARTISTS = (
    FeaturedArtist("Acid Pauli", "Organic House / Downtempo", "Psychedelische, verspielte Elektronik", "https://acidpauli.bandcamp.com/album/vola"),
    FeaturedArtist("Viken Arman", "Downtempo / Electronica", "Jazzige Texturen und langsame Grooves", "https://vikenarman.bandcamp.com/album/the-light-at-the-end"),
    FeaturedArtist("Be Svendsen", "Downtempo / Slow House", "Warme, erzählerische Clubmusik", "https://besvendsen.bandcamp.com/album/man-on-the-run-remixes"),
    FeaturedArtist("Nico Stojan", "Deep House / Downtempo", "Melodischer, organischer Sound", "https://solselectas.bandcamp.com/album/summer-sol-iii"),
)
