"""Image preview tools."""

from annotools import config
from annotools.image.grid import GridOptions, draw_grid
from annotools.server import mcp
from annotools.tools.common import (
    DEFAULT_OUTPUT_FORMAT,
    AllowUpscaleParam,
    CropParam,
    GridColor,
    GridMode,
    MaxHeightParam,
    MaxWidthParam,
    McpImage,
    OutputFormatParam,
    PreviewOptions,
    SaveToParam,
    SourceParam,
    TargetPixelsParam,
    finish,
    render_preview,
)

PREVIEW_PARAMS_DOC = "Coordinates are normalized 0-1 relative to the uncropped source."


def _options(**kwargs) -> PreviewOptions:
    return PreviewOptions(**kwargs)


def _with_grid(result, grid: GridOptions | None, extra: dict) -> None:
    if grid is not None:
        gridded = draw_grid(result.image, grid)
        result.image = gridded.image
        extra.update(gridded.metadata)


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
    options = _options(
        source=source,
        crop=crop,
        target_pixels=target_pixels,
        max_width=max_width,
        max_height=max_height,
        allow_upscale=allow_upscale,
        output_format=output_format,
        save_to=save_to,
    )
    return finish(render_preview(options), options)


@mcp.tool(output_schema=None)
def preview_image_grid(
    source: SourceParam,
    columns: int = config.GRID_COLUMNS,
    rows: int = config.GRID_ROWS,
    mode: GridMode = "ratio",
    column_width: int | None = None,
    row_width: int | None = None,
    color: GridColor = "white",
    opacity: float = config.GRID_OPACITY,
    line_width: int = config.GRID_LINE_WIDTH,
    crop: CropParam = None,
    target_pixels: TargetPixelsParam = None,
    max_width: MaxWidthParam = config.MAX_PREVIEW_WIDTH,
    max_height: MaxHeightParam = config.MAX_PREVIEW_HEIGHT,
    allow_upscale: AllowUpscaleParam = False,
    output_format: OutputFormatParam = DEFAULT_OUTPUT_FORMAT,
    save_to: SaveToParam = None,
) -> list[McpImage | str]:
    """Preview an image with a semi-transparent grid (default 10x10 cells, 50% white) to anchor positions.

    Returns the image and one JSON metadata object including `grid` step sizes in normalized coordinates
    of the cropped view. Coordinates are normalized 0-1 relative to the uncropped source.
    """
    options = _options(
        source=source,
        crop=crop,
        target_pixels=target_pixels,
        max_width=max_width,
        max_height=max_height,
        allow_upscale=allow_upscale,
        output_format=output_format,
        save_to=save_to,
    )
    result = render_preview(options)
    extra: dict = {}
    _with_grid(
        result,
        GridOptions(
            columns=columns,
            rows=rows,
            mode=mode,
            column_width=column_width,
            row_width=row_width,
            color=color,
            opacity=opacity,
            line_width=line_width,
        ),
        extra,
    )
    return finish(result, options, extra=extra)
