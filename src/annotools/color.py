"""Color parsing, stable text-to-color hashing, and helpers."""

import colorsys
import hashlib

from PIL import ImageColor

__all__ = [
    "RGB",
    "color_from_text",
    "parse_color",
    "to_hex",
]

RGB = tuple[int, int, int]


def parse_color(value: str, name: str = "color") -> RGB:
    """Parse a CSS/PIL color name or ``#RRGGBB`` into an RGB tuple.

    Raises:
        ValueError: naming ``name`` when the value is not a recognised color.
    """
    try:
        r, g, b = ImageColor.getrgb(value)[:3]
    except ValueError as exc:
        raise ValueError(f"{name}: {value!r} is not a color name or #RRGGBB value") from exc
    return (r, g, b)


def text_color_for(background: RGB) -> RGB:
    """Return black or white, whichever reads better on ``background``."""
    r, g, b = background
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return (0, 0, 0) if luminance > 150 else (255, 255, 255)


def color_from_text(text: str) -> RGB:
    """Map any text to a stable, saturated color (sha256 → hue; S = 0.75, L = 0.5).

    Identical text always yields the same color; a one-character change yields an unrelated one.
    """
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    hue = int.from_bytes(digest[:2], "big") / 65536
    r, g, b = colorsys.hls_to_rgb(hue, 0.5, 0.75)
    return (round(r * 255), round(g * 255), round(b * 255))


def to_hex(color: RGB) -> str:
    """Format an RGB tuple as lowercase ``#rrggbb``."""
    return "#{:02x}{:02x}{:02x}".format(*color)
