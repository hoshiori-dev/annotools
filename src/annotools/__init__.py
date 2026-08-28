"""annotools: see and annotate multimodal data within an MLLM token budget.

Two ways in:

- ``annotools.mcp`` — the MCP server (``annotools`` command) that coding agents call; not imported here.
- this package — the library layer for agent developers. Everything listed in ``__all__`` is the public
  API (stable within a minor version); module paths such as ``annotools.image.preview`` stay importable.
  Nothing here imports ``fastmcp``.
"""

from importlib.metadata import PackageNotFoundError, version

from annotools.audio import clip_audio
from annotools.color import RGB, color_from_text, parse_color, to_hex
from annotools.config import GridMode, OutputFormat, Settings, configure, get_settings, reset_settings
from annotools.geometry import (
    FULL_FRAME,
    AxisOrder,
    Box,
    Coordinates,
    PixelBox,
    RotatedBox,
    denormalize_coordinates,
    fit_size,
    is_rectangle,
    normalize_coordinates,
    rotated_box_to_corners,
    validate_normalized_box,
    validate_normalized_point,
)
from annotools.image.grid import GridOptions, draw_grid
from annotools.image.overlay import (
    BBoxObject,
    KeypointObject,
    PolygonObject,
    draw_bboxes,
    draw_keypoints,
    draw_polygons,
)
from annotools.image.preview import PreviewResult, encode, preview
from annotools.image.segmentation import MASK_MODES, load_mask, overlay_mask
from annotools.io import load_image, open_bytes, write_bytes
from annotools.video import sample_frames

try:
    __version__ = version("annotools")
except PackageNotFoundError:  # pragma: no cover - only when running from an unbuilt checkout
    __version__ = "0.0.0"

__all__ = [
    "FULL_FRAME",
    "MASK_MODES",
    "RGB",
    "AxisOrder",
    "BBoxObject",
    "Box",
    "Coordinates",
    "GridMode",
    "GridOptions",
    "KeypointObject",
    "OutputFormat",
    "PixelBox",
    "PolygonObject",
    "PreviewResult",
    "RotatedBox",
    "Settings",
    "__version__",
    "clip_audio",
    "color_from_text",
    "configure",
    "denormalize_coordinates",
    "draw_bboxes",
    "draw_grid",
    "draw_keypoints",
    "draw_polygons",
    "encode",
    "fit_size",
    "get_settings",
    "is_rectangle",
    "load_image",
    "load_mask",
    "normalize_coordinates",
    "open_bytes",
    "overlay_mask",
    "parse_color",
    "preview",
    "reset_settings",
    "rotated_box_to_corners",
    "sample_frames",
    "to_hex",
    "validate_normalized_box",
    "validate_normalized_point",
    "write_bytes",
]
