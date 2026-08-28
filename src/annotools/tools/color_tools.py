"""Color helper tools."""

from typing import Annotated

from pydantic import BaseModel, Field

from annotools.app import mcp
from annotools.color import color_from_text as _color_from_text
from annotools.color import to_hex


class ColorResult(BaseModel):
    """A color as hex string and RGB triple."""

    hex: str = Field(description="Lowercase #rrggbb")
    rgb: tuple[int, int, int] = Field(description="Red, green, blue in 0-255")


@mcp.tool
def color_from_text(text: Annotated[str, Field(description="Any text, e.g. a label or an instance id")]) -> ColorResult:
    """Return a stable, saturated color for any text: same text, same color; different text, unrelated color."""
    rgb = _color_from_text(text)
    return ColorResult(hex=to_hex(rgb), rgb=rgb)
