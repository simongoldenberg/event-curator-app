"""Öffentliche Defaults; persönliche Einstellungen werden ausschließlich lokal gelesen."""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
EXPORTS = ROOT / "exports"
PROFILE = DATA / "user_party_profile.json"
SOURCES = DATA / "user_sources.json"
STATE = DATA / "user_monthly_state.json"
REGIONS = {
    "Würzburg": (49.7913, 9.9534, "DE", ("würzburg", "wuerzburg", "wurzburg")),
    "Freiburg": (47.9990, 7.8421, "DE", ("freiburg", "freiburg im breisgau")),
    "Wien": (48.2082, 16.3738, "AT", ("wien", "vienna")),
    "Berlin": (52.5200, 13.4050, "DE", ("berlin",)),
    "Frankfurt": (50.1109, 8.6821, "DE", ("frankfurt", "frankfurt am main")),
}
DEFAULT_RADIUS_KM = 50
REGION_MIN_RADII_KM = {"Würzburg": 100}


def radius_for_region(name, profile):
    """Würzburg gezielt ausweiten; ein größerer persönlicher Radius bleibt erhalten."""
    return max(profile.get("radius_km", DEFAULT_RADIUS_KM), REGION_MIN_RADII_KM.get(name, 0))


def load_env(path=ROOT / ".env"):
    """Liest einfache KEY=VALUE-Einträge, ohne Shell-Auswertung."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep or key.strip() != "BANDSINTOWN_APP_ID":
            continue
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
