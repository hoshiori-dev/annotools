"""Image preview tools."""

from annotools import config
from annotools.image.grid import GridOptions, draw_grid
from annotools.image.overlay import (
    BBoxObject,
    KeypointObject,
    PolygonObject,
    draw_bboxes,
    draw_keypoints,
    draw_polygons,
)
from annotools.server import mcp
from annotools.tools.common import (
    DEFAULT_OUTPUT_FORMAT,
    AllowUpscaleParam,
    CropParam,
    GridColor,
    GridMode,
    LineWidthParam,
    MaxHeightParam,
    MaxWidthParam,
    McpImage,
    OutputFormatParam,
    PointDiameterParam,
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


@mcp.tool(output_schema=None)
def preview_image_bboxes(
    source: SourceParam,
    objects: list[BBoxObject],
    grid: GridOptions | None = None,
    line_width: LineWidthParam = config.DEFAULT_LINE_WIDTH,
    crop: CropParam = None,
    target_pixels: TargetPixelsParam = None,
    max_width: MaxWidthParam = config.MAX_PREVIEW_WIDTH,
    max_height: MaxHeightParam = config.MAX_PREVIEW_HEIGHT,
    allow_upscale: AllowUpscaleParam = False,
    output_format: OutputFormatParam = DEFAULT_OUTPUT_FORMAT,
    save_to: SaveToParam = None,
) -> list[McpImage | str]:
    """Preview an image with bounding boxes (normalized xyxy, optional labels), optionally over a grid.

    Use it to check candidate detections before writing them to the database. Returns the image and one
    JSON metadata object (base keys, `grid` when used, `objects` count).
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
    _with_grid(result, grid, extra)
    drawn = draw_bboxes(result, objects, line_width=line_width)
    extra["objects"] = drawn.metadata["objects"]
    return finish(drawn, options, extra=extra)


@mcp.tool(output_schema=None)
def preview_image_keypoints(
    source: SourceParam,
    objects: list[KeypointObject],
    grid: GridOptions | None = None,
    point_diameter: PointDiameterParam = config.DEFAULT_POINT_DIAMETER,
    crop: CropParam = None,
    target_pixels: TargetPixelsParam = None,
    max_width: MaxWidthParam = config.MAX_PREVIEW_WIDTH,
    max_height: MaxHeightParam = config.MAX_PREVIEW_HEIGHT,
    allow_upscale: AllowUpscaleParam = False,
    output_format: OutputFormatParam = DEFAULT_OUTPUT_FORMAT,
    save_to: SaveToParam = None,
) -> list[McpImage | str]:
    """Preview an image with keypoints (normalized xy, optional labels) drawn as dots, optionally over a grid.

    Returns the image and one JSON metadata object (base keys, `grid` when used, `objects` count).
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
    _with_grid(result, grid, extra)
    drawn = draw_keypoints(result, objects, point_diameter=point_diameter)
    extra["objects"] = drawn.metadata["objects"]
    return finish(drawn, options, extra=extra)


@mcp.tool(output_schema=None)
def preview_image_polygons(
    source: SourceParam,
    objects: list[PolygonObject],
    grid: GridOptions | None = None,
    line_width: LineWidthParam = config.DEFAULT_LINE_WIDTH,
    point_diameter: PointDiameterParam = config.DEFAULT_POINT_DIAMETER,
    show_point_index: bool = True,
    crop: CropParam = None,
    target_pixels: TargetPixelsParam = None,
    max_width: MaxWidthParam = config.MAX_PREVIEW_WIDTH,
    max_height: MaxHeightParam = config.MAX_PREVIEW_HEIGHT,
    allow_upscale: AllowUpscaleParam = False,
    output_format: OutputFormatParam = DEFAULT_OUTPUT_FORMAT,
    save_to: SaveToParam = None,
) -> list[McpImage | str]:
    """Preview an image with polygons (flat normalized [x1, y1, x2, y2, ...]) with vertex dots and indices.

    Works for COCO-style outlines and DOTA-style rotated boxes (4 corners). Returns the image and one JSON
    metadata object (base keys, `grid` when used, `objects` count).
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
    _with_grid(result, grid, extra)
    drawn = draw_polygons(
        result, objects, line_width=line_width, point_diameter=point_diameter, show_point_index=show_point_index
    )
    extra["objects"] = drawn.metadata["objects"]
    return finish(drawn, options, extra=extra)
