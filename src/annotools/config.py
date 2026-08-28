"""Project-wide defaults, resolved once from CLI arguments, ``ANNOTOOLS_*`` environment variables, and code."""

from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from annotools.color import parse_color

__all__ = [
    "GridMode",
    "OutputFormat",
    "Settings",
    "configure",
    "get_settings",
    "reset_settings",
]

OutputFormat = Literal["jpeg", "png", "webp"]
"""Encodings a preview can be returned in."""
GridMode = Literal["ratio", "fixed"]
"""``ratio``: a fixed number of equal cells; ``fixed``: cells of a given pixel size."""


class Settings(BaseSettings):
    """Process-wide defaults for previews, grids, overlays, and encoding.

    One object serves both audiences: the ``annotools`` command resolves it once from flags and
    ``ANNOTOOLS_*`` variables and bakes the values into the MCP tool schemas; library callers read it
    through [`get_settings`][annotools.get_settings] at call time, so every ``None`` parameter falls back to these
    values.

    Precedence: ``annotools`` command-line flags (``--max-width``), then ``ANNOTOOLS_<FIELD>``
    environment variables (``ANNOTOOLS_MAX_WIDTH``), then the field defaults. Empty environment values
    are ignored; invalid values raise a ``pydantic.ValidationError`` naming the field.

    Examples:
        >>> from annotools import Settings
        >>> Settings(max_width=768, grid_columns=8).grid_columns
        8

    References:
        - Spec: ``.agents/knowledge/spec/mcp-overview.md`` (annotools repository), settings table.
        - 384 px default: Gemini bills an image up to 384x384 as one 258-token unit,
          https://ai.google.dev/gemini-api/docs/image-understanding (verified 2026-08-27); Claude and
          GPT bill by area, so pass 768+ for them (``skills/mllm-multimodal-input``).
    """

    model_config = SettingsConfigDict(env_prefix="ANNOTOOLS_", env_ignore_empty=True, extra="ignore")

    max_width: int = Field(384, ge=1, description="Maximum preview width in pixels")
    max_height: int = Field(384, ge=1, description="Maximum preview height in pixels")
    target_pixels: int | None = Field(None, ge=1, description="Cap on preview area in pixels (null = none)")
    grid_columns: int = Field(10, ge=1, description="Grid cells per row")
    grid_rows: int = Field(10, ge=1, description="Grid cells per column")
    grid_mode: GridMode = Field(
        "ratio", description="ratio: equal cells; fixed: cells of grid_column_width x grid_row_width"
    )
    grid_column_width: int | None = Field(None, ge=1, description="Grid cell width in output pixels (fixed mode)")
    grid_row_width: int | None = Field(None, ge=1, description="Grid cell height in output pixels (fixed mode)")
    grid_opacity: float = Field(0.5, ge=0.0, le=1.0, description="Grid line opacity")
    grid_line_width: int = Field(1, ge=1, description="Grid line width in output pixels")
    line_width: int = Field(2, ge=1, description="Outline width of boxes and polygons in output pixels")
    point_diameter: int = Field(3, ge=1, description="Keypoint and vertex dot diameter in output pixels")
    color: str = Field("blue", description="Default overlay color (name or #RRGGBB)")
    output_format: OutputFormat = Field("jpeg", description="Default encoding of returned previews")
    jpeg_quality: int = Field(90, ge=1, le=100, description="JPEG quality")

    @field_validator("color")
    @classmethod
    def _color_parses(cls, value: str) -> str:
        parse_color(value, name="color")
        return value

    @model_validator(mode="after")
    def _fixed_grid_needs_widths(self) -> "Settings":
        if self.grid_mode == "fixed" and (self.grid_column_width is None or self.grid_row_width is None):
            raise ValueError("grid_column_width and grid_row_width are required when grid_mode='fixed'")
        return self


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the process-wide [`Settings`][annotools.Settings], resolving them from the environment on first use.

    Library functions call this whenever a parameter is ``None``; the result is cached until
    [`configure`][annotools.configure] or [`reset_settings`][annotools.reset_settings] replaces it.

    Returns:
        The active settings object (shared, not a copy).

    Examples:
        >>> from annotools import get_settings
        >>> get_settings().max_width
        384
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def configure(settings: Settings) -> None:
    """Replace the process-wide settings.

    Library functions read [`get_settings`][annotools.get_settings] at call time, so the new values apply to every later
    call. The MCP tool schemas snapshot the settings when ``annotools.mcp.server`` is first imported;
    call this before that import (as ``annotools.mcp.cli`` does) to change the defaults the server
    advertises.

    Args:
        settings: The settings to install, typically built from flags or code.

    Examples:
        >>> from annotools import Settings, configure, get_settings, reset_settings
        >>> configure(Settings(max_width=200))
        >>> get_settings().max_width
        200
        >>> reset_settings()
    """
    global _settings
    _settings = settings


def reset_settings() -> None:
    """Forget the resolved settings so the next [`get_settings`][annotools.get_settings] reads the environment again.

    Meant for tests and interactive sessions; production code calls [`configure`][annotools.configure] instead.

    Examples:
        >>> from annotools import Settings, configure, get_settings, reset_settings
        >>> configure(Settings(max_width=200))
        >>> reset_settings()
        >>> get_settings().max_width
        384
    """
    global _settings
    _settings = None
