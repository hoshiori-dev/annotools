"""Image preview tools."""

from annotools import config
from annotools.image.preview import preview
from annotools.server import mcp
from annotools.tools.common import (
    DEFAULT_OUTPUT_FORMAT,
    AllowUpscaleParam,
    CropParam,
    MaxHeightParam,
    MaxWidthParam,
    McpImage,
    OutputFormatParam,
    PreviewOptions,
    SaveToParam,
    SourceParam,
    TargetPixelsParam,
    finish,
    load_source,
)


@mcp.tool(output_schema=None)
def preview_image(
    source: SourceParam,
    crop: CropParam = None,
    target_pixels: TargetPixelsParam = None,
    max_width: MaxWidthParam = config.MAX_PREVIEW_WIDTH,
    max_height: MaxHeightParam = config.MAX_PREVIEW_HEIGHT,
    allow_upscale: AllowUpscaleParam = False,
    output_format: OutputFormatParam = DEFAULT_OUTPUT_FORMAT,
    save_to: SaveToParam = None,
) -> list[McpImage | str]:
    """Downscale an image (optionally zoomed to a normalized crop box) to fit a token budget.

    Returns the image followed by one JSON metadata object (original_size, crop, output_size, scale,
    format). Coordinates are normalized 0-1 relative to the uncropped source.
    """
    options = PreviewOptions(
        source=source,
        crop=crop,
        target_pixels=target_pixels,
        max_width=max_width,
        max_height=max_height,
        allow_upscale=allow_upscale,
        output_format=output_format,
        save_to=save_to,
    )
    result = preview(
        load_source(options),
        crop=options.crop,
        target_pixels=options.target_pixels,
        max_width=options.max_width,
        max_height=options.max_height,
        allow_upscale=options.allow_upscale,
    )
    return finish(result, options)
