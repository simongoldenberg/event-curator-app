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
    FeaturedArtist("Caleesi", "Melodische Elektronik", "Verträumte Sets, solo und mit Sarah Kreis", "https://klunkerkranich.org/events/2025-07-12-mystic-tales-above-the-clouds-w-caleesi-mcfly-mia-kober-weam-ismael-mohii-danielle-pineapple-ezqizita/"),
    FeaturedArtist("Just Emma", "Deep / Melodic / Downtempo", "Verspielte, organische Clubmusik", "https://soundcloud.com/justemmaoffical"),
)
