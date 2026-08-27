"""Parameter models and helpers shared by the MCP tool wrappers."""

import json
from typing import Annotated, Any, Literal, cast

from fastmcp.utilities.types import Image as McpImage
from pydantic import BaseModel, Field

from annotools import config
from annotools.image.preview import PreviewResult, encode, preview
from annotools.io import load_image, write_bytes

OutputFormat = Literal["jpeg", "png", "webp"]
GridMode = Literal["ratio", "fixed"]
GridColor = Literal["white", "black", "invert"]
DEFAULT_OUTPUT_FORMAT: OutputFormat = cast(OutputFormat, config.DEFAULT_OUTPUT_FORMAT)

# Annotated parameter types reused by every tool signature so descriptions and constraints reach the schema.
SourceParam = Annotated[
    str, Field(description="Local path or fsspec URL (file://, s3://, gs://, http(s)://, memory://)")
]
CropParam = Annotated[
    tuple[float, float, float, float] | None,
    Field(description="Normalized [x_min, y_min, x_max, y_max] of the source to zoom into (0-1, min < max)"),
]
TargetPixelsParam = Annotated[int | None, Field(ge=1, description="Cap on output area in pixels")]
MaxWidthParam = Annotated[int, Field(ge=1, description="Maximum output width in pixels")]
MaxHeightParam = Annotated[int, Field(ge=1, description="Maximum output height in pixels")]
AllowUpscaleParam = Annotated[bool, Field(description="Enlarge small images/regions up to the limits")]
OutputFormatParam = Annotated[OutputFormat, Field(description="Encoding: jpeg (quality 90), png, or webp")]
SaveToParam = Annotated[str | None, Field(description="Also write the encoded image to this path or fsspec URL")]
LineWidthParam = Annotated[int, Field(ge=1, description="Outline width in output pixels")]
GridCellsParam = Annotated[int, Field(ge=1, description="Number of grid cells along this axis")]
GridCellSizeParam = Annotated[int | None, Field(ge=1, description="Cell size in output pixels (mode='fixed')")]
GridOpacityParam = Annotated[float, Field(ge=0.0, le=1.0, description="Line opacity, 0 (invisible) to 1 (solid)")]
GridLineWidthParam = Annotated[int, Field(ge=1, description="Grid line width in output pixels")]
PointDiameterParam = Annotated[int, Field(ge=1, description="Vertex/point dot diameter in output pixels")]


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
    output_format: OutputFormat = Field(default=DEFAULT_OUTPUT_FORMAT)
    save_to: str | None = Field(default=None, description="Also write the encoded image to this path/URL")


def render_preview(options: PreviewOptions) -> PreviewResult:
    """Load the source named by ``options`` and render the plain preview."""
    return preview(
        load_image(options.source),
        crop=options.crop,
        target_pixels=options.target_pixels,
        max_width=options.max_width,
        max_height=options.max_height,
        allow_upscale=options.allow_upscale,
    )


def preview_options(**kwargs: Any) -> PreviewOptions:
    """Build ``PreviewOptions`` from a tool's flat keyword arguments."""
    return PreviewOptions(**kwargs)


def finish(result: PreviewResult, options: PreviewOptions, extra: dict[str, Any] | None = None) -> list[McpImage | str]:
    """Encode a preview result into the MCP return shape ``[Image, metadata JSON]``."""
    data = encode(result.image, options.output_format)
    metadata = {**result.metadata, "format": options.output_format, **(extra or {})}
    if options.save_to:
        write_bytes(options.save_to, data)
        metadata["saved_to"] = options.save_to
    return [McpImage(data=data, format=options.output_format), json.dumps(metadata)]
