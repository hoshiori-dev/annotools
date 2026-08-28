"""Annotation overlays (bounding boxes, keypoints, polygons) drawn on a rendered preview."""

from collections.abc import Sequence

from pydantic import BaseModel, Field

from annotools.color import parse_color
from annotools.config import get_settings
from annotools.geometry import validate_normalized_box, validate_normalized_point
from annotools.image._draw import canvas, draw_dot, draw_label
from annotools.image.preview import PreviewResult

__all__ = [
    "BBoxObject",
    "KeypointObject",
    "PolygonObject",
    "draw_bboxes",
    "draw_keypoints",
    "draw_polygons",
]


class BBoxObject(BaseModel):
    """A bounding box in normalized coordinates of the uncropped source.

    Examples:
        >>> from annotools import BBoxObject
        >>> BBoxObject(bbox=(0.1, 0.1, 0.5, 0.5), label="cat").color is None
        True
    """

    bbox: tuple[float, float, float, float] = Field(description="(x_min, y_min, x_max, y_max), normalized 0-1")
    label: str | None = Field(default=None, description="Optional text drawn above the box")
    color: str | None = Field(default=None, description="Color name or #RRGGBB; None uses Settings.color")


class KeypointObject(BaseModel):
    """A single point in normalized coordinates of the uncropped source.

    Examples:
        >>> from annotools import KeypointObject
        >>> KeypointObject(point=(0.5, 0.5), label="nose").label
        'nose'
    """

    point: tuple[float, float] = Field(description="(x, y), normalized 0-1")
    label: str | None = Field(default=None, description="Optional text drawn beside the point")
    color: str | None = Field(default=None, description="Color name or #RRGGBB; None uses Settings.color")


class PolygonObject(BaseModel):
    """A closed polygon as a flat list of normalized coordinates of the uncropped source.

    Examples:
        >>> from annotools import PolygonObject
        >>> len(PolygonObject(points=[0.1, 0.1, 0.5, 0.1, 0.1, 0.5]).points)
        6
    """

    points: list[float] = Field(description="[x1, y1, x2, y2, ...], even count, at least 3 points, normalized 0-1")
    label: str | None = Field(default=None, description="Optional text drawn at the first vertex")
    color: str | None = Field(default=None, description="Color name or #RRGGBB; None uses Settings.color")


class _Mapper:
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
        """Whether an output pixel coordinate lies within the image (edges inclusive)."""
        return 0 <= px <= self.width and 0 <= py <= self.height


def draw_bboxes(result: PreviewResult, objects: Sequence[BBoxObject], line_width: int | None = None) -> PreviewResult:
    """Draw ``objects`` on ``result.image`` (in place) and add the ``objects`` count to the metadata.

    Boxes are given in source coordinates and mapped through the preview's ``crop`` and ``scale``, so
    the same objects can be drawn on the full view and on a zoomed crop. Boxes entirely outside the
    view are skipped but still counted; partially visible ones are clipped.

    Args:
        result: A preview from [`preview`][annotools.preview] (with or without a grid); RGB/RGBA images are drawn on in
            place, other modes are converted to a new RGB image.
        objects: At least one box; ``label`` is drawn as a tag above the box, ``color`` defaults to
            ``Settings.color``.
        line_width: Outline width in output pixels; ``None`` uses ``Settings.line_width`` (2).

    Returns:
        The same image wrapped with ``metadata["objects"]`` = number of boxes.

    Raises:
        ValueError: For empty ``objects``, an invalid box or color (naming ``objects[i]``), or
            ``line_width < 1``.

    Examples:
        >>> from PIL import Image
        >>> from annotools import BBoxObject, draw_bboxes, preview
        >>> result = preview(
        ...     Image.new("RGB", (400, 300), "white"), max_width=400, max_height=400
        ... )
        >>> draw_bboxes(
        ...     result, [BBoxObject(bbox=(0.1, 0.1, 0.5, 0.5), label="cat")]
        ... ).metadata["objects"]
        1

    References:
        - Spec: ``.agents/knowledge/spec/preview-image-bboxes.md`` (annotools repository).
    """
    if not objects:
        raise ValueError("objects: at least one bounding box is required")
    settings = get_settings()
    line_width = settings.line_width if line_width is None else line_width
    if line_width < 1:
        raise ValueError(f"line_width must be >= 1, got {line_width}")
    mapper = _Mapper(result)
    image, draw = canvas(result)
    for index, obj in enumerate(objects):
        box = validate_normalized_box(obj.bbox, name=f"objects[{index}].bbox")
        color = parse_color(settings.color if obj.color is None else obj.color, name=f"objects[{index}].color")
        x0, y0 = mapper.to_pixels(box[0], box[1])
        x1, y1 = mapper.to_pixels(box[2], box[3])
        if x1 < 0 or y1 < 0 or x0 > mapper.width or y0 > mapper.height:
            continue
        # The outline band starts at the mapped edge and extends inward by line_width.
        draw.rectangle((round(x0), round(y0), round(x1) - 1, round(y1) - 1), outline=color, width=line_width)
        if obj.label:
            draw_label(draw, obj.label, round(x0), round(y0), color, image.size)
    return PreviewResult(image=image, metadata={**result.metadata, "objects": len(objects)})


def draw_keypoints(
    result: PreviewResult, objects: Sequence[KeypointObject], point_diameter: int | None = None
) -> PreviewResult:
    """Draw ``objects`` as filled dots (optional labels) and add the ``objects`` count to the metadata.

    Args:
        result: A preview from [`preview`][annotools.preview]; its image is modified.
        objects: At least one point; ``label`` is drawn beside the dot, ``color`` defaults to
            ``Settings.color``.
        point_diameter: Dot diameter in output pixels; ``None`` uses ``Settings.point_diameter`` (3).

    Returns:
        The same image wrapped with ``metadata["objects"]`` = number of points.

    Raises:
        ValueError: For empty ``objects``, a point outside [0, 1] or an unknown color (naming
            ``objects[i]``), or ``point_diameter < 1``.

    Examples:
        >>> from PIL import Image
        >>> from annotools import KeypointObject, draw_keypoints, preview
        >>> result = preview(
        ...     Image.new("RGB", (400, 300), "white"), max_width=400, max_height=400
        ... )
        >>> draw_keypoints(result, [KeypointObject(point=(0.5, 0.5))]).metadata["objects"]
        1

    References:
        - Spec: ``.agents/knowledge/spec/preview-image-keypoints.md`` (annotools repository).
    """
    if not objects:
        raise ValueError("objects: at least one keypoint is required")
    settings = get_settings()
    point_diameter = settings.point_diameter if point_diameter is None else point_diameter
    if point_diameter < 1:
        raise ValueError(f"point_diameter must be >= 1, got {point_diameter}")
    mapper = _Mapper(result)
    image, draw = canvas(result)
    for index, obj in enumerate(objects):
        x, y = validate_normalized_point(obj.point, name=f"objects[{index}].point")
        color = parse_color(settings.color if obj.color is None else obj.color, name=f"objects[{index}].color")
        px, py = mapper.to_pixels(x, y)
        if not mapper.inside(px, py):
            continue
        draw_dot(draw, px, py, point_diameter, color)
        if obj.label:
            draw_label(draw, obj.label, px + point_diameter, py, color, image.size, anchor="middle")
    return PreviewResult(image=image, metadata={**result.metadata, "objects": len(objects)})


def _validate_polygon(points: Sequence[float], name: str) -> list[tuple[float, float]]:
    """Return the vertex list after checking count parity, minimum size, and range."""
    if len(points) % 2 or len(points) < 6:
        raise ValueError(f"{name}: expected an even number of values for at least 3 points, got {len(points)} values")
    return [validate_normalized_point(points[i : i + 2], name=f"{name}[{i // 2}]") for i in range(0, len(points), 2)]


def draw_polygons(
    result: PreviewResult,
    objects: Sequence[PolygonObject],
    line_width: int | None = None,
    point_diameter: int | None = None,
    show_point_index: bool = True,
) -> PreviewResult:
    """Draw closed polygons with vertex dots and optional 1-based vertex indices; add ``objects`` to metadata.

    Vertex indices let a model refer to "point 3" when correcting a polygon, which is why they are on
    by default. Polygons with no vertex inside the view are skipped but still counted.

    Args:
        result: A preview from [`preview`][annotools.preview]; its image is modified.
        objects: At least one polygon (``points`` even-length, at least 3 vertices); ``color`` defaults
            to ``Settings.color``.
        line_width: Outline width in output pixels; ``None`` uses ``Settings.line_width`` (2).
        point_diameter: Vertex dot diameter; ``None`` uses ``Settings.point_diameter`` (3).
        show_point_index: Draw the 1-based vertex number next to each vertex.

    Returns:
        The same image wrapped with ``metadata["objects"]`` = number of polygons.

    Raises:
        ValueError: For empty ``objects``, an invalid polygon or color (naming ``objects[i]``), or a
            width or diameter smaller than 1.

    Examples:
        >>> from PIL import Image
        >>> from annotools import PolygonObject, draw_polygons, preview
        >>> result = preview(
        ...     Image.new("RGB", (400, 300), "white"), max_width=400, max_height=400
        ... )
        >>> draw_polygons(
        ...     result, [PolygonObject(points=[0.1, 0.1, 0.5, 0.1, 0.1, 0.5])]
        ... ).metadata["objects"]
        1

    References:
        - Spec: ``.agents/knowledge/spec/preview-image-polygons.md`` (annotools repository).
    """
    if not objects:
        raise ValueError("objects: at least one polygon is required")
    settings = get_settings()
    line_width = settings.line_width if line_width is None else line_width
    point_diameter = settings.point_diameter if point_diameter is None else point_diameter
    if line_width < 1 or point_diameter < 1:
        raise ValueError(f"line_width and point_diameter must be >= 1, got {line_width} and {point_diameter}")
    mapper = _Mapper(result)
    image, draw = canvas(result)
    for index, obj in enumerate(objects):
        vertices = _validate_polygon(obj.points, name=f"objects[{index}].points")
        color = parse_color(settings.color if obj.color is None else obj.color, name=f"objects[{index}].color")
        pixels = [mapper.to_pixels(x, y) for x, y in vertices]
        if not any(mapper.inside(px, py) for px, py in pixels):
            continue
        draw.line([*pixels, pixels[0]], fill=color, width=line_width, joint="curve")
        cx = sum(px for px, _ in pixels) / len(pixels)
        cy = sum(py for _, py in pixels) / len(pixels)
        for number, (px, py) in enumerate(pixels, start=1):
            draw_dot(draw, px, py, point_diameter, color)
            if show_point_index:
                dx, dy = (px - cx), (py - cy)
                norm = max(1e-6, (dx * dx + dy * dy) ** 0.5)
                offset = point_diameter + 8
                draw_label(draw, str(number), px + dx / norm * offset, py + dy / norm * offset, color, image.size)
        if obj.label:
            draw_label(draw, obj.label, pixels[0][0], pixels[0][1] - point_diameter - 12, color, image.size)
    return PreviewResult(image=image, metadata={**result.metadata, "objects": len(objects)})
