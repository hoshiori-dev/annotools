"""Image preview tools."""

from typing import Annotated, Literal

from pydantic import Field

from annotools.config import get_settings
from annotools.image.grid import GridOptions, draw_grid
from annotools.image.overlay import (
    BBoxObject,
    KeypointObject,
    PolygonObject,
    draw_bboxes,
    draw_keypoints,
    draw_polygons,
)
from annotools.image.segmentation import load_mask, overlay_mask
from annotools.server import mcp
from annotools.tools.common import (
    DEFAULT_OUTPUT_FORMAT,
    AllowUpscaleParam,
    CropParam,
    GridCellSizeParam,
    GridCellsParam,
    GridColor,
    GridLineWidthParam,
    GridMode,
    GridOpacityParam,
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

settings = get_settings()

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
    target_pixels: TargetPixelsParam = settings.target_pixels,
    max_width: MaxWidthParam = settings.max_width,
    max_height: MaxHeightParam = settings.max_height,
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
    columns: GridCellsParam = settings.grid_columns,
    rows: GridCellsParam = settings.grid_rows,
    mode: GridMode = settings.grid_mode,
    column_width: GridCellSizeParam = settings.grid_column_width,
    row_width: GridCellSizeParam = settings.grid_row_width,
    color: GridColor = "white",
    opacity: GridOpacityParam = settings.grid_opacity,
    line_width: GridLineWidthParam = settings.grid_line_width,
    crop: CropParam = None,
    target_pixels: TargetPixelsParam = settings.target_pixels,
    max_width: MaxWidthParam = settings.max_width,
    max_height: MaxHeightParam = settings.max_height,
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
    line_width: LineWidthParam = settings.line_width,
    crop: CropParam = None,
    target_pixels: TargetPixelsParam = settings.target_pixels,
    max_width: MaxWidthParam = settings.max_width,
    max_height: MaxHeightParam = settings.max_height,
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
    point_diameter: PointDiameterParam = settings.point_diameter,
    crop: CropParam = None,
    target_pixels: TargetPixelsParam = settings.target_pixels,
    max_width: MaxWidthParam = settings.max_width,
    max_height: MaxHeightParam = settings.max_height,
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
    line_width: LineWidthParam = settings.line_width,
    point_diameter: PointDiameterParam = settings.point_diameter,
    show_point_index: bool = True,
    crop: CropParam = None,
    target_pixels: TargetPixelsParam = settings.target_pixels,
    max_width: MaxWidthParam = settings.max_width,
    max_height: MaxHeightParam = settings.max_height,
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


@mcp.tool(output_schema=None)
def preview_image_segmentation(
    source: SourceParam,
    mask_source: Annotated[str, Field(description="Single-channel ID mask (uint8/uint16 PNG/TIFF); 0 = background")],
    annotation: Annotated[
        Literal["label", "legend"], Field(description="label: ID at each region; legend: strip below")
    ] = "label",
    id_names: Annotated[dict[int, str] | None, Field(description="Optional display names per ID")] = None,
    alpha: Annotated[float, Field(ge=0.0, le=1.0, description="Blend strength of region colours")] = 0.5,
    line_width: Annotated[
        int, Field(ge=0, description="Region outline width in output pixels; 0 disables")
    ] = settings.line_width,
    grid: GridOptions | None = None,
    crop: CropParam = None,
    target_pixels: TargetPixelsParam = settings.target_pixels,
    max_width: MaxWidthParam = settings.max_width,
    max_height: MaxHeightParam = settings.max_height,
    allow_upscale: AllowUpscaleParam = False,
    output_format: OutputFormatParam = DEFAULT_OUTPUT_FORMAT,
    save_to: SaveToParam = None,
) -> list[McpImage | str]:
    """Preview an image with an ID mask (instance/panoptic/semantic) blended on top, labelled or with a legend.

    Regions are coloured with color_from_text(str(id)). Returns the image and one JSON metadata object
    (base keys, `grid` when used, `ids`, and `legend` in legend mode).
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
    result.metadata.update(extra)  # so a legend re-fit can rescale the grid's pixel cell sizes
    drawn = overlay_mask(
        result,
        load_mask(mask_source),
        annotation=annotation,
        id_names=id_names,
        alpha=alpha,
        line_width=line_width,
        max_width=max_width,
        max_height=max_height,
        target_pixels=target_pixels,
    )
    extra.pop("grid", None)  # drawn.metadata carries the grid, rescaled by the legend re-fit if any
    extra["ids"] = drawn.metadata["ids"]
    if "legend" in drawn.metadata:
        extra["legend"] = drawn.metadata["legend"]
        extra["image_size"] = drawn.metadata["image_size"]
    return finish(drawn, options, extra=extra)
