"""Mapping of species keys to their photo files in the assets/ folder."""

import os

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# species_key → filename inside ASSETS_DIR
SPECIES_PHOTOS: dict[str, str] = {
    "steppe_cat":     "Степной кот.png",
    "jungle_cat":     "Камышовый кот.png",
    "sand_cat":       "Барханный кот.png",
    "caracal":        "каракал.jpg",
    "turkestan_lynx": "туркестанская рысь.jpg",
    "snow_leopard":   "снежный барс.png",
    # "unsure" intentionally has no photo
}


def photo_bytes(species_key: str) -> bytes | None:
    """Return raw bytes for the species photo, or None if not found."""
    filename = SPECIES_PHOTOS.get(species_key)
    if not filename:
        return None
    path = os.path.join(ASSETS_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()
