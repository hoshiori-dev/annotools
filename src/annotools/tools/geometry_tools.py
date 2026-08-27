"""Geometry conversion tools."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from annotools.geometry import RotatedBox, rotated_box_to_corners
from annotools.server import mcp


class PolygonsResult(BaseModel):
    """Corner lists, one per input box."""

    polygons: list[list[float]] = Field(description="[x1, y1, x2, y2, x3, y3, x4, y4] per box, clockwise from top-left")


@mcp.tool
def rotated_bbox_to_polygon(
    boxes: Annotated[
        list[RotatedBox], Field(min_length=1, description="Rotated boxes (cx, cy, w, h, theta), normalized")
    ],
    angle_unit: Annotated[Literal["degrees", "radians"], Field(description="Unit of every theta")] = "degrees",
    aspect_ratio: Annotated[float, Field(gt=0, description="Source width / height; 1.0 assumes a square image")] = 1.0,
) -> PolygonsResult:
    """Convert rotated boxes (cx, cy, w, h, theta; theta clockwise) into DOTA-style 8-number corner polygons.

    Corners are not clipped: a box touching the border can yield coordinates outside 0-1, which
    preview_image_polygons rejects — clamp or shrink such boxes before previewing them. Pass the source
    aspect ratio so rotation on non-square images does not shear.
    """
    polygons = [
        rotated_box_to_corners(box, angle_unit=angle_unit, aspect_ratio=aspect_ratio, name=f"boxes[{i}]")
        for i, box in enumerate(boxes)
    ]
    return PolygonsResult(polygons=polygons)
