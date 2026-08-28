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
GridMode = Literal["ratio", "fixed"]


class Settings(BaseSettings):
    """Defaults for every preview tool.

    Precedence: ``annotools`` command-line flags (``--max-width``), then ``ANNOTOOLS_<FIELD>``
    environment variables (``ANNOTOOLS_MAX_WIDTH``), then the values below. Empty environment values are
    ignored.
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
    """Return the process-wide settings, resolving them from the environment on first use."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def configure(settings: Settings) -> None:
    """Replace the process-wide settings.

    Library functions read ``get_settings()`` at call time, so the new values apply to every later call.
    The MCP tool schemas snapshot the settings when ``annotools.mcp.server`` is first imported; call
    this before that import (as ``annotools.mcp.cli`` does) to change the defaults the server advertises.
    """
    global _settings
    _settings = settings


def reset_settings() -> None:
    """Forget the resolved settings (tests only)."""
    global _settings
    _settings = None
