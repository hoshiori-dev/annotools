"""Annotation overlays (bounding boxes, keypoints, polygons) drawn on a rendered preview."""

from collections.abc import Sequence

from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field

from annotools import config
from annotools.color import RGB, parse_color, text_color_for
from annotools.geometry import validate_normalized_box, validate_normalized_point
from annotools.image.preview import PreviewResult


class BBoxObject(BaseModel):
    """A bounding box in normalized coordinates of the uncropped source."""

    bbox: tuple[float, float, float, float] = Field(description="(x_min, y_min, x_max, y_max), normalized 0-1")
    label: str | None = Field(default=None, description="Optional text drawn above the box")
    color: str = Field(default=config.DEFAULT_COLOR, description="Color name or #RRGGBB")


class KeypointObject(BaseModel):
    """A single point in normalized coordinates of the uncropped source."""

    point: tuple[float, float] = Field(description="(x, y), normalized 0-1")
    label: str | None = Field(default=None, description="Optional text drawn beside the point")
    color: str = Field(default=config.DEFAULT_COLOR, description="Color name or #RRGGBB")


class PolygonObject(BaseModel):
    """A closed polygon as a flat list of normalized coordinates of the uncropped source."""

    points: list[float] = Field(description="[x1, y1, x2, y2, ...], even count, at least 3 points, normalized 0-1")
    label: str | None = Field(default=None, description="Optional text drawn at the first vertex")
    color: str = Field(default=config.DEFAULT_COLOR, description="Color name or #RRGGBB")


class Mapper:
    """Maps normalized source coordinates to output pixels of a rendered preview."""

    def __init__(self, result: PreviewResult) -> None:
        """Build the mapping from a rendered preview and its ``crop`` metadata."""
        x_min, y_min, x_max, y_max = result.metadata["crop"]
        self.width, self.height = result.image.size
        self.x_min, self.y_min = x_min, y_min
        self.span_x, self.span_y = x_max - x_min, y_max - y_min

    def to_pixels(self, x: float, y: float) -> tuple[float, float]:
        """Return output pixel coordinates for a normalized source point (may fall outside the image)."""
        return ((x - self.x_min) / self.span_x * self.width, (y - self.y_min) / self.span_y * self.height)

    def inside(self, px: float, py: float) -> bool:
        """Whether an output pixel coordinate lies within the image."""
        return 0 <= px < self.width and 0 <= py < self.height


def _canvas(result: PreviewResult) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = result.image if result.image.mode in ("RGB", "RGBA") else result.image.convert("RGB")
    return image, ImageDraw.Draw(image)


def _draw_dot(draw: ImageDraw.ImageDraw, px: float, py: float, diameter: int, color: RGB) -> None:
    r = diameter / 2
    draw.ellipse((px - r, py - r, px + r, py + r), fill=color)


def _draw_label(draw: ImageDraw.ImageDraw, text: str, x: float, y: float, color: RGB, size: tuple[int, int]) -> None:
    font = ImageFont.load_default()
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    tw, th = right - left + 4, bottom - top + 4
    tx = min(max(0, x), max(0, size[0] - tw))
    ty = y - th if y - th >= 0 else y
    draw.rectangle((tx, ty, tx + tw, ty + th), fill=color)
    draw.text((tx + 2 - left, ty + 2 - top), text, fill=text_color_for(color), font=font)


def draw_bboxes(
    result: PreviewResult, objects: Sequence[BBoxObject], line_width: int = config.DEFAULT_LINE_WIDTH
) -> PreviewResult:
    """Draw ``objects`` on ``result.image`` (in place) and add ``objects`` count to the metadata.

    Raises:
        ValueError: for empty ``objects``, an invalid box or color (naming ``objects[i]``), or ``line_width < 1``.
    """
    if not objects:
        raise ValueError("objects: at least one bounding box is required")
    if line_width < 1:
        raise ValueError(f"line_width must be >= 1, got {line_width}")
    mapper = Mapper(result)
    image, draw = _canvas(result)
    for index, obj in enumerate(objects):
        box = validate_normalized_box(obj.bbox, name=f"objects[{index}].bbox")
        color = parse_color(obj.color, name=f"objects[{index}].color")
        x0, y0 = mapper.to_pixels(box[0], box[1])
        x1, y1 = mapper.to_pixels(box[2], box[3])
        if x1 < 0 or y1 < 0 or x0 > mapper.width or y0 > mapper.height:
            continue
        # The outline band starts at the mapped edge and extends inward by line_width.
        draw.rectangle((round(x0), round(y0), round(x1) - 1, round(y1) - 1), outline=color, width=line_width)
        if obj.label:
            _draw_label(draw, obj.label, round(x0), round(y0), color, image.size)
    return PreviewResult(image=image, metadata={**result.metadata, "objects": len(objects)})


def draw_keypoints(
    result: PreviewResult, objects: Sequence[KeypointObject], point_diameter: int = config.DEFAULT_POINT_DIAMETER
) -> PreviewResult:
    """Draw ``objects`` as filled dots (optional labels) and add ``objects`` count to the metadata.

    Raises:
        ValueError: for empty ``objects``, a point outside [0, 1] or an unknown color (naming ``objects[i]``),
            or ``point_diameter < 1``.
    """
    if not objects:
        raise ValueError("objects: at least one keypoint is required")
    if point_diameter < 1:
        raise ValueError(f"point_diameter must be >= 1, got {point_diameter}")
    mapper = Mapper(result)
    image, draw = _canvas(result)
    for index, obj in enumerate(objects):
        x, y = validate_normalized_point(obj.point, name=f"objects[{index}].point")
        color = parse_color(obj.color, name=f"objects[{index}].color")
        px, py = mapper.to_pixels(x, y)
        if not mapper.inside(px, py):
            continue
        _draw_dot(draw, px, py, point_diameter, color)
        if obj.label:
            _draw_label(draw, obj.label, px + point_diameter, py, color, image.size)
    return PreviewResult(image=image, metadata={**result.metadata, "objects": len(objects)})


def validate_polygon(points: Sequence[float], name: str) -> list[tuple[float, float]]:
    """Return the vertex list after checking count parity, minimum size, and range.

    Raises:
        ValueError: naming ``name`` on any violation.
    """
    if len(points) % 2 or len(points) < 6:
        raise ValueError(f"{name}: expected an even number of values for at least 3 points, got {len(points)} values")
    return [validate_normalized_point(points[i : i + 2], name=f"{name}[{i // 2}]") for i in range(0, len(points), 2)]


def draw_polygons(
    result: PreviewResult,
    objects: Sequence[PolygonObject],
    line_width: int = config.DEFAULT_LINE_WIDTH,
    point_diameter: int = config.DEFAULT_POINT_DIAMETER,
    show_point_index: bool = True,
) -> PreviewResult:
    """Draw closed polygons with vertex dots and optional 1-based vertex indices; add ``objects`` to metadata.

    Raises:
        ValueError: for empty ``objects``, an invalid polygon or color (naming ``objects[i]``), or a width or
            diameter smaller than 1.
    """
    if not objects:
        raise ValueError("objects: at least one polygon is required")
    if line_width < 1 or point_diameter < 1:
        raise ValueError(f"line_width and point_diameter must be >= 1, got {line_width} and {point_diameter}")
    mapper = Mapper(result)
    image, draw = _canvas(result)
    for index, obj in enumerate(objects):
        vertices = validate_polygon(obj.points, name=f"objects[{index}].points")
        color = parse_color(obj.color, name=f"objects[{index}].color")
        pixels = [mapper.to_pixels(x, y) for x, y in vertices]
        if not any(mapper.inside(px, py) for px, py in pixels):
            continue
        draw.line([*pixels, pixels[0]], fill=color, width=line_width, joint="curve")
        cx = sum(px for px, _ in pixels) / len(pixels)
        cy = sum(py for _, py in pixels) / len(pixels)
        for number, (px, py) in enumerate(pixels, start=1):
            _draw_dot(draw, px, py, point_diameter, color)
            if show_point_index:
                dx, dy = (px - cx), (py - cy)
                norm = max(1e-6, (dx * dx + dy * dy) ** 0.5)
                offset = point_diameter + 8
                _draw_label(draw, str(number), px + dx / norm * offset, py + dy / norm * offset, color, image.size)
        if obj.label:
            _draw_label(draw, obj.label, pixels[0][0], pixels[0][1] - point_diameter - 12, color, image.size)
    return PreviewResult(image=image, metadata={**result.metadata, "objects": len(objects)})
