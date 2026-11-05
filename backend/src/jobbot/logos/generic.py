"""Images génériques à ne pas prendre pour un logo (docs/14 §4).

Une page d'offre ou un e-mail d'alerte montre parfois une image de la source à la place du
logo de l'entreprise (carré vide, pixel de suivi, silhouette). Elle est refusée si :
- son empreinte est dans BANNED (trouvées en production) ;
- la même image est déjà celle d'au moins SHARED_LIMIT autres entreprises ;
- elle est presque vide : moins de MIN_SIDE px de côté, moins de MIN_OPAQUE de pixels
  visibles, ou un aplat d'une seule couleur hors transparence.
"""

import hashlib
import io
import re
import warnings

from PIL import Image

MIN_SIDE = 24
MIN_OPAQUE = 0.02
SHARED_LIMIT = 2
# Une valeur d'alpha en dessous est tenue pour transparente.
ALPHA_VISIBLE = 16
# Écart par canal toléré pour « une seule couleur » (bruit de compression JPEG).
COLOR_TOLERANCE = 8
# Part de l'image couverte par un aplat d'une seule couleur pour qu'il soit refusé.
FLAT_COVER = 0.9
# Au-delà, l'image n'est pas décodée (largement assez grande pour être un logo).
MAX_PIXELS = 4_000_000

# Empreintes sha256 d'images génériques relevées en production (diagnostic du 2026-11-05).
BANNED: frozenset[str] = frozenset()

_SVG_TAG = re.compile(rb"<svg\b[^>]*>", re.I | re.S)
_LENGTH = re.compile(r"^\s*([0-9]*\.?[0-9]+)\s*(px)?\s*$", re.I)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _svg_attribute(tag: str, name: str) -> float | None:
    found = re.search(rf"\s{name}\s*=\s*[\"']([^\"']*)[\"']", tag, re.I)
    if not found:
        return None
    length = _LENGTH.match(found.group(1))
    return float(length.group(1)) if length else None


def _svg_reason(data: bytes) -> str | None:
    """SVG : seule la taille déclarée (width, height en px) est vérifiée, sans rasteriser."""
    tag = _SVG_TAG.search(data[:4000])
    if not tag:
        return None
    text = tag.group(0).decode("utf-8", errors="replace")
    sides = [v for v in (_svg_attribute(text, "width"), _svg_attribute(text, "height")) if v]
    if sides and min(sides) < MIN_SIDE:
        return "image trop petite"
    return None


def _raster_reason(data: bytes) -> str | None:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as image:
                width, height = image.size
                if min(width, height) < MIN_SIDE:
                    return "image trop petite"
                if width * height > MAX_PIXELS:
                    return None
                rgba = image.convert("RGBA")
    except (OSError, ValueError, Image.DecompressionBombWarning, Image.DecompressionBombError):
        return "image illisible"
    visible = rgba.getchannel("A").point(lambda a: 255 if a >= ALPHA_VISIBLE else 0)
    opaque = visible.histogram()[255]
    if opaque < MIN_OPAQUE * width * height:
        return "image presque transparente"
    # Histogramme des seuls pixels visibles, par canal : bornes de chaque couleur.
    histogram = rgba.convert("RGB").histogram(mask=visible)
    extrema = []
    for band in range(3):
        counts = histogram[band * 256 : (band + 1) * 256]
        used = [value for value, count in enumerate(counts) if count]
        extrema.append((used[0], used[-1]))
    # Un logo d'une seule couleur sur fond transparent (texte noir, sigle blanc) garde sa
    # forme : seul l'aplat qui couvre presque toute l'image est refusé.
    flat = all(high - low <= COLOR_TOLERANCE for low, high in extrema)
    if flat and opaque >= FLAT_COVER * width * height:
        return "une seule couleur"
    return None


def blank_reason(data: bytes, media_type: str) -> str | None:
    """Pourquoi l'image est presque vide ; None si elle peut servir de logo."""
    if media_type == "image/svg+xml":
        return _svg_reason(data)
    return _raster_reason(data)


def refusal(data: bytes, media_type: str, others: int) -> str | None:
    """Pourquoi l'image n'est pas un logo ; `others` : autres entreprises avec la même image."""
    if sha256(data) in BANNED:
        return "image générique connue"
    if others >= SHARED_LIMIT:
        return "image commune à plusieurs entreprises"
    return blank_reason(data, media_type)
