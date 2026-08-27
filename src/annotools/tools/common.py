"""Parameter models and helpers shared by the MCP tool wrappers."""

import json
from typing import Any, Literal

from fastmcp.utilities.types import Image as McpImage
from pydantic import BaseModel, Field

from annotools import config
from annotools.image.preview import PreviewResult, encode
from annotools.io import load_image, write_bytes

OutputFormat = Literal["jpeg", "png", "webp"]


class PreviewOptions(BaseModel):
    """Parameters shared by every preview tool (see docs/spec/mcp-overview.md)."""

    source: str = Field(description="Local path or fsspec URL of the image")
    crop: tuple[float, float, float, float] | None = Field(
        default=None, description="Normalized (x_min, y_min, x_max, y_max) region to zoom into"
    )
    target_pixels: int | None = Field(default=None, ge=1, description="Cap on output area in pixels")
    max_width: int = Field(default=config.MAX_PREVIEW_WIDTH, ge=1)
    max_height: int = Field(default=config.MAX_PREVIEW_HEIGHT, ge=1)
    allow_upscale: bool = Field(default=False, description="Allow enlarging small images/regions up to the limits")
    output_format: OutputFormat = Field(default="jpeg")  # type: ignore[assignment]
    save_to: str | None = Field(default=None, description="Also write the encoded image to this path/URL")


def load_source(options: PreviewOptions):
    """Load the source image named by ``options``."""
    return load_image(options.source)


def finish(result: PreviewResult, options: PreviewOptions, extra: dict[str, Any] | None = None) -> list[McpImage | str]:
    """Encode a preview result into the MCP return shape ``[Image, metadata JSON]``."""
    data = encode(result.image, options.output_format)
    metadata = {**result.metadata, "format": options.output_format, **(extra or {})}
    if options.save_to:
        write_bytes(options.save_to, data)
        metadata["saved_to"] = options.save_to
    return [McpImage(data=data, format=options.output_format), json.dumps(metadata)]
