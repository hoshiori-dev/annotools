"""Geometry conversion tools."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from annotools import geometry
from annotools.geometry import RotatedBox, rotated_box_to_corners
from annotools.server import mcp
from annotools.tools.common import CropParam

CoordinatesParam = Annotated[
    list[list[float]],
    Field(
        min_length=1,
        description="Entries of flat x, y, x, y, ... values (point, box, polygon); y, x per pair when axis_order='yx'",
    ),
]
NormalizedCoordinatesParam = Annotated[
    list[list[float]],
    Field(min_length=1, description="Entries of flat x, y, x, y, ... values in [0, 1] (always x-first)"),
]
BaseWidthParam = Annotated[
    float,
    Field(
        gt=0,
        description="Width of the frame the coordinates refer to: the preview output_width, or 1000 for 0-1000 outputs",
    ),
]
BaseHeightParam = Annotated[float, Field(gt=0, description="Height of that frame: output_height, or 1000")]
AxisOrderParam = Annotated[
    Literal["xy", "yx"],
    Field(description="Pair order on the base-frame side only (yx for Gemini's [ymin, xmin, ymax, xmax])"),
]


class CoordinatesResult(BaseModel):
    """Converted entries, same shape as the input."""

    coordinates: list[list[float]] = Field(description="One flat list per input entry")


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


@mcp.tool
def normalize_coordinates(
    coordinates: CoordinatesParam,
    base_width: BaseWidthParam,
    base_height: BaseHeightParam,
    crop: CropParam = None,
    axis_order: AxisOrderParam = "xy",
) -> CoordinatesResult:
    """Convert a model's coordinates into the storage convention (normalized 0-1, x-first, uncropped source).

    Ask each model in its native convention, then pass its answer here with the frame it used: for pixel
    answers (Claude, Qwen2.5-VL) base_width/base_height are the preview's output_width/output_height; for
    0-1000 answers (Gemini, Qwen3-VL) or 0-999 (GPT) use 1000 or 999. Pass the preview's crop so a zoomed
    view maps back into the full image. Results are clamped to [0, 1].
    """
    return CoordinatesResult(
        coordinates=geometry.normalize_coordinates(
            coordinates, base_width, base_height, crop=crop, axis_order=axis_order
        )
    )


@mcp.tool
def denormalize_coordinates(
    coordinates: NormalizedCoordinatesParam,
    base_width: BaseWidthParam,
    base_height: BaseHeightParam,
    crop: CropParam = None,
    axis_order: AxisOrderParam = "xy",
) -> CoordinatesResult:
    """Convert stored normalized coordinates into a model's frame (pixels of a preview or a 0-1000 space).

    The inverse of normalize_coordinates: the input is normalized 0-1 relative to the uncropped source,
    the output is in the base_width x base_height frame of the given crop (y-first pairs when
    axis_order='yx'). Values are not clamped, so a point outside the crop maps outside the frame.
    """
    return CoordinatesResult(
        coordinates=geometry.denormalize_coordinates(
            coordinates, base_width, base_height, crop=crop, axis_order=axis_order
        )
    )
