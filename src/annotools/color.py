"""Color parsing and helpers."""

from PIL import ImageColor

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
