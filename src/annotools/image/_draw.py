"""Internal: PIL drawing helpers shared by the overlay and segmentation modules."""

from PIL import Image, ImageDraw, ImageFont

from annotools.color import RGB, text_color_for
from annotools.image.preview import PreviewResult


def canvas(result: PreviewResult) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = result.image if result.image.mode in ("RGB", "RGBA") else result.image.convert("RGB")
    return image, ImageDraw.Draw(image)


def draw_dot(draw: ImageDraw.ImageDraw, px: float, py: float, diameter: int, color: RGB) -> None:
    r = diameter / 2
    draw.ellipse((px - r, py - r, px + r, py + r), fill=color)


def draw_label(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: float,
    y: float,
    color: RGB,
    size: tuple[int, int],
    anchor: str = "above",
) -> None:
    """Draw a filled tag with ``text`` near (x, y), kept fully inside ``size``."""
    font = ImageFont.load_default()
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    tw, th = right - left + 4, bottom - top + 4
    ty = y - th / 2 if anchor == "middle" else (y - th if y - th >= 0 else y)
    tx = min(max(0, x), max(0, size[0] - tw))
    ty = min(max(0, ty), max(0, size[1] - th))
    draw.rectangle((tx, ty, tx + tw, ty + th), fill=color)
    draw.text((tx + 2 - left, ty + 2 - top), text, fill=text_color_for(color), font=font)
