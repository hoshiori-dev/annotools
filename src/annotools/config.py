"""Project-wide defaults. Every value can be overridden with an ``ANNOTOOLS_<NAME>`` environment variable."""

import os


def _env(name: str, default: int | float | str) -> int | float | str:
    raw = os.environ.get(f"ANNOTOOLS_{name}")
    if raw is None:
        return default
    return type(default)(raw)


MAX_PREVIEW_WIDTH: int = int(_env("MAX_PREVIEW_WIDTH", 768))
MAX_PREVIEW_HEIGHT: int = int(_env("MAX_PREVIEW_HEIGHT", 768))
DEFAULT_LINE_WIDTH: int = int(_env("DEFAULT_LINE_WIDTH", 2))
DEFAULT_POINT_DIAMETER: int = int(_env("DEFAULT_POINT_DIAMETER", 3))
GRID_COLUMNS: int = int(_env("GRID_COLUMNS", 10))
GRID_ROWS: int = int(_env("GRID_ROWS", 10))
GRID_OPACITY: float = float(_env("GRID_OPACITY", 0.5))
GRID_LINE_WIDTH: int = int(_env("GRID_LINE_WIDTH", 1))
DEFAULT_COLOR: str = str(_env("DEFAULT_COLOR", "blue"))
DEFAULT_OUTPUT_FORMAT: str = str(_env("DEFAULT_OUTPUT_FORMAT", "jpeg"))
JPEG_QUALITY: int = int(_env("JPEG_QUALITY", 90))
