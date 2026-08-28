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

    Args:
        value: Color name (``"blue"``) or hex string (``"#0000ff"``), as accepted by Pillow.
        name: Prefix used in the error message so callers can point at the offending field.

    Returns:
        ``(r, g, b)`` with each channel in 0-255.

    Raises:
        ValueError: Naming ``name`` when the value is not a recognised color.

    Examples:
        >>> from annotools import parse_color
        >>> parse_color("red"), parse_color("#0000ff")
        ((255, 0, 0), (0, 0, 255))
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
    """Map any text to a stable, saturated color.

    The hue comes from the first two bytes of ``sha256(text)``; saturation is 0.75 and lightness 0.5,
    which keeps every color readable on both light and dark backgrounds. Identical text always yields
    the same color and a one-character change yields an unrelated one, so labels and mask IDs get
    consistent colors across runs without a lookup table.

    Args:
        text: Any string (a class name, a mask ID rendered as text).

    Returns:
        ``(r, g, b)`` with each channel in 0-255.

    Examples:
        >>> from annotools import color_from_text, to_hex
        >>> color_from_text("cat") == color_from_text("cat")
        True
        >>> to_hex(color_from_text("cat")).startswith("#")
        True

    References:
        - Spec: ``.agents/knowledge/spec/color-from-text.md`` (annotools repository).
    """
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    hue = int.from_bytes(digest[:2], "big") / 65536
    r, g, b = colorsys.hls_to_rgb(hue, 0.5, 0.75)
    return (round(r * 255), round(g * 255), round(b * 255))


def to_hex(color: RGB) -> str:
    """Format an RGB tuple as lowercase ``#rrggbb``.

    Args:
        color: ``(r, g, b)`` with each channel in 0-255.

    Returns:
        The seven-character hex string.

    Examples:
        >>> from annotools import to_hex
        >>> to_hex((255, 0, 0))
        '#ff0000'
    """
    return "#{:02x}{:02x}{:02x}".format(*color)
