"""Project-wide defaults. Every value can be overridden with an ``ANNOTOOLS_<NAME>`` environment variable."""

import os


def _env(name: str, default: int | float | str) -> int | float | str:
    """Return ``ANNOTOOLS_<name>`` converted to the default's type, or the default.

    Raises:
        ValueError: naming the variable when it cannot be converted.
    """
    raw = os.environ.get(f"ANNOTOOLS_{name}")
    if raw is None or raw == "":
        return default
    try:
        return type(default)(raw)
    except ValueError as exc:
        raise ValueError(f"ANNOTOOLS_{name}={raw!r} is not a valid {type(default).__name__}") from exc


def _positive(name: str, default: int) -> int:
    value = int(_env(name, default))
    if value < 1:
        raise ValueError(f"ANNOTOOLS_{name} must be >= 1, got {value}")
    return value


MAX_PREVIEW_WIDTH: int = _positive("MAX_PREVIEW_WIDTH", 768)
MAX_PREVIEW_HEIGHT: int = _positive("MAX_PREVIEW_HEIGHT", 768)
DEFAULT_LINE_WIDTH: int = _positive("DEFAULT_LINE_WIDTH", 2)
DEFAULT_POINT_DIAMETER: int = _positive("DEFAULT_POINT_DIAMETER", 3)
GRID_COLUMNS: int = _positive("GRID_COLUMNS", 10)
GRID_ROWS: int = _positive("GRID_ROWS", 10)
GRID_OPACITY: float = float(_env("GRID_OPACITY", 0.5))
GRID_LINE_WIDTH: int = _positive("GRID_LINE_WIDTH", 1)
DEFAULT_COLOR: str = str(_env("DEFAULT_COLOR", "blue"))
DEFAULT_OUTPUT_FORMAT: str = str(_env("DEFAULT_OUTPUT_FORMAT", "jpeg"))
JPEG_QUALITY: int = _positive("JPEG_QUALITY", 90)

if not 0.0 <= GRID_OPACITY <= 1.0:
    raise ValueError(f"ANNOTOOLS_GRID_OPACITY must be within [0, 1], got {GRID_OPACITY}")
if DEFAULT_OUTPUT_FORMAT not in ("jpeg", "png", "webp"):
    raise ValueError(f"ANNOTOOLS_DEFAULT_OUTPUT_FORMAT must be jpeg, png, or webp, got {DEFAULT_OUTPUT_FORMAT!r}")
