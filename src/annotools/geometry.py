"""Coordinate helpers. Tool-facing coordinates are normalized to [0, 1] relative to the uncropped source."""

import math
from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel, Field

Box = tuple[float, float, float, float]
PixelBox = tuple[int, int, int, int]
FULL_FRAME: Box = (0.0, 0.0, 1.0, 1.0)


def validate_normalized_box(box: Sequence[float], name: str = "box") -> Box:
    """Return ``box`` as a tuple after checking range and ordering.

    Raises:
        ValueError: with ``name`` in the message when a value is outside [0, 1] or min >= max.
    """
    if len(box) != 4:
        raise ValueError(f"{name}: expected 4 values (x_min, y_min, x_max, y_max), got {len(box)}")
    x_min, y_min, x_max, y_max = (float(v) for v in box)
    for label, value in (("x_min", x_min), ("y_min", y_min), ("x_max", x_max), ("y_max", y_max)):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name}: {label}={value} is outside [0, 1]")
    if x_min >= x_max or y_min >= y_max:
        raise ValueError(f"{name}: min must be smaller than max, got {(x_min, y_min, x_max, y_max)}")
    return (x_min, y_min, x_max, y_max)


def validate_normalized_point(point: Sequence[float], name: str = "point") -> tuple[float, float]:
    """Return ``point`` as a tuple after checking both values are within [0, 1]."""
    if len(point) != 2:
        raise ValueError(f"{name}: expected 2 values (x, y), got {len(point)}")
    x, y = float(point[0]), float(point[1])
    if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
        raise ValueError(f"{name}: ({x}, {y}) is outside [0, 1]")
    return (x, y)


def normalized_box_to_pixels(box: Box, width: int, height: int) -> PixelBox:
    """Map a normalized box to integer pixel bounds, rounded outward so the region never shrinks."""
    x_min, y_min, x_max, y_max = box
    return (
        max(0, math.floor(x_min * width)),
        max(0, math.floor(y_min * height)),
        min(width, math.ceil(x_max * width)),
        min(height, math.ceil(y_max * height)),
    )


def fit_size(
    width: int,
    height: int,
    *,
    max_width: int,
    max_height: int,
    target_pixels: int | None = None,
    allow_upscale: bool = False,
) -> tuple[int, int]:
    """Scale ``(width, height)`` to fit the limits, preserving aspect ratio.

    The output never exceeds ``max_width`` x ``max_height`` nor ``target_pixels`` (area). Without
    ``allow_upscale`` the output never exceeds the input size either.

    Raises:
        ValueError: when a limit is smaller than 1.
    """
    if max_width < 1 or max_height < 1:
        raise ValueError(f"max_width/max_height must be >= 1, got {max_width}x{max_height}")
    if target_pixels is not None and target_pixels < 1:
        raise ValueError(f"target_pixels must be >= 1, got {target_pixels}")
    scale = min(max_width / width, max_height / height)
    if target_pixels is not None:
        scale = min(scale, math.sqrt(target_pixels / (width * height)))
    if not allow_upscale:
        scale = min(scale, 1.0)
    # Round to the nearest pixel (floor undershoots binding limits by 1 px through floating point),
    # then fall back to floor if rounding would break a cap.
    out_w, out_h = max(1, round(width * scale)), max(1, round(height * scale))
    if out_w > max_width or out_h > max_height or (target_pixels is not None and out_w * out_h > target_pixels):
        out_w, out_h = max(1, math.floor(width * scale)), max(1, math.floor(height * scale))
    if not allow_upscale:
        out_w, out_h = min(out_w, width), min(out_h, height)
    return (out_w, out_h)


class RotatedBox(BaseModel):
    """A rotated box: normalized centre and size plus a clockwise rotation about the centre."""

    cx: float = Field(description="Centre x, normalized 0-1")
    cy: float = Field(description="Centre y, normalized 0-1")
    w: float = Field(description="Width, normalized (> 0)")
    h: float = Field(description="Height, normalized (> 0)")
    theta: float = Field(description="Clockwise rotation about the centre (image coordinates, y down)")


def rotated_box_to_corners(
    box: RotatedBox,
    *,
    angle_unit: Literal["degrees", "radians"] = "degrees",
    aspect_ratio: float = 1.0,
    name: str = "box",
) -> list[float]:
    """Return the 4 corners of ``box`` as ``[x1, y1, ..., x4, y4]``, clockwise from the unrotated top-left.

    Rotation is performed in an isotropic frame (x scaled by ``aspect_ratio`` = source width / height) so
    boxes on non-square images rotate without shear. Corners are not clipped to [0, 1].

    Raises:
        ValueError: naming ``name`` for a non-positive size, a centre outside [0, 1], or a bad aspect ratio.
    """
    if aspect_ratio <= 0:
        raise ValueError(f"aspect_ratio must be > 0, got {aspect_ratio}")
    if box.w <= 0:
        raise ValueError(f"{name}.w must be > 0, got {box.w}")
    if box.h <= 0:
        raise ValueError(f"{name}.h must be > 0, got {box.h}")
    if not 0.0 <= box.cx <= 1.0:
        raise ValueError(f"{name}.cx={box.cx} is outside [0, 1]")
    if not 0.0 <= box.cy <= 1.0:
        raise ValueError(f"{name}.cy={box.cy} is outside [0, 1]")
    theta = box.theta if angle_unit == "radians" else math.radians(box.theta)
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    half_w, half_h = box.w * aspect_ratio / 2, box.h / 2
    corners: list[float] = []
    for dx, dy in ((-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)):
        # clockwise rotation with y pointing down is the standard rotation matrix
        rx, ry = dx * cos_t - dy * sin_t, dx * sin_t + dy * cos_t
        corners.extend((box.cx + rx / aspect_ratio, box.cy + ry))
    return corners


def is_rectangle(points: Sequence[float], angle_tol_deg: float = 2.0, length_tol: float = 0.02) -> bool:
    """Whether the flat ``[x1, y1, ..., x4, y4]`` polygon is a rectangle within tolerances.

    Adjacent edges must be perpendicular within ``angle_tol_deg`` and opposite edges equal in length
    within ``length_tol`` (relative). Anything other than 4 points returns False.
    """
    if len(points) != 8:
        return False
    pts = [(points[i], points[i + 1]) for i in range(0, 8, 2)]
    edges = [(pts[(i + 1) % 4][0] - pts[i][0], pts[(i + 1) % 4][1] - pts[i][1]) for i in range(4)]
    lengths = [math.hypot(*e) for e in edges]
    if min(lengths) == 0:
        return False
    for i in range(4):
        a, b = edges[i], edges[(i + 1) % 4]
        cos_angle = (a[0] * b[0] + a[1] * b[1]) / (lengths[i] * lengths[(i + 1) % 4])
        if abs(math.degrees(math.acos(max(-1.0, min(1.0, cos_angle)))) - 90) > angle_tol_deg:
            return False
    return all(abs(lengths[i] - lengths[i + 2]) / max(lengths[i], lengths[i + 2]) <= length_tol for i in range(2))
