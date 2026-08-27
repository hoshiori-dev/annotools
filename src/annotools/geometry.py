"""Coordinate helpers. Tool-facing coordinates are normalized to [0, 1] relative to the uncropped source."""

import math
from collections.abc import Sequence

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
    return (max(1, math.floor(width * scale)), max(1, math.floor(height * scale)))
