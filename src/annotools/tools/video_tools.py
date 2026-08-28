"""Video preview tools: sampled frames rendered through the image preview pipeline."""

import json
from typing import Annotated, Any

from pydantic import Field

from annotools.app import mcp
from annotools.config import get_settings
from annotools.image.grid import GridOptions
from annotools.image.preview import encode, preview
from annotools.io import write_bytes
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
    MaxHeightParam,
    MaxWidthParam,
    McpImage,
    OutputFormatParam,
    PreviewOptions,
    SourceParam,
    TargetPixelsParam,
)
from annotools.tools.image_tools import _with_grid
from annotools.video import sample_frames

settings = get_settings()

FpsParam = Annotated[float, Field(gt=0, description="Target sampling rate in frames per second")]
StartParam = Annotated[float | None, Field(ge=0, description="Start time in seconds")]
EndParam = Annotated[float | None, Field(gt=0, description="End time in seconds (exclusive)")]
MaxFramesParam = Annotated[int, Field(ge=1, description="Hard cap on returned frames; extra frames are thinned evenly")]
SaveDirParam = Annotated[
    str | None,
    Field(description="Directory (path or fsspec URL) to write the frames into as frame_<index>_<time>.<ext>"),
]


def _render_frames(
    options: PreviewOptions,
    fps: float,
    start: float | None,
    end: float | None,
    max_frames: int,
    grid: GridOptions | None,
) -> list:
    frames, info = sample_frames(options.source, fps=fps, start=start, end=end, max_frames=max_frames)
    blocks: list[Any] = []
    metadata: dict[str, Any] = {}
    timestamps: list[float] = []
    for index, (timestamp, image) in enumerate(frames):
        result = preview(
            image,
            crop=options.crop,
            target_pixels=options.target_pixels,
            max_width=options.max_width,
            max_height=options.max_height,
            allow_upscale=options.allow_upscale,
        )
        if index == 0:
            metadata.update(result.metadata)
        _with_grid(result, grid, metadata)
        data = encode(result.image, options.output_format)
        if options.save_to:
            name = f"frame_{index:04d}_{timestamp:.3f}.{options.output_format}"
            write_bytes(f"{options.save_to.rstrip('/')}/{name}", data)
        blocks.append(McpImage(data=data, format=options.output_format))
        timestamps.append(round(timestamp, 3))
    metadata.update(
        {
            "format": options.output_format,
            "frames": len(frames),
            "timestamps": timestamps,
            "duration": round(info["duration"], 3),
            "requested_fps": info["requested_fps"],
            "thinned": info["thinned"],
        }
    )
    if options.save_to:
        metadata["saved_to"] = options.save_to
    blocks.append(json.dumps(metadata))
    return blocks


@mcp.tool(output_schema=None)
def preview_video(
    source: SourceParam,
    fps: FpsParam = 1.0,
    start: StartParam = None,
    end: EndParam = None,
    max_frames: MaxFramesParam = 32,
    crop: CropParam = None,
    target_pixels: TargetPixelsParam = settings.target_pixels,
    max_width: MaxWidthParam = settings.max_width,
    max_height: MaxHeightParam = settings.max_height,
    allow_upscale: AllowUpscaleParam = False,
    output_format: OutputFormatParam = DEFAULT_OUTPUT_FORMAT,
    save_to: SaveDirParam = None,
) -> list[McpImage | str]:
    """Sample a video at `fps` (default 1 frame/s, at most `max_frames`) and preview each frame at a bounded size.

    Returns the frames in time order followed by one JSON metadata object (timestamps, duration,
    thinning, first-frame size/crop/scale). `save_to` is a directory for the frame files.
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
    return _render_frames(options, fps, start, end, max_frames, None)


@mcp.tool(output_schema=None)
def preview_video_grid(
    source: SourceParam,
    fps: FpsParam = 1.0,
    start: StartParam = None,
    end: EndParam = None,
    max_frames: MaxFramesParam = 32,
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
    save_to: SaveDirParam = None,
) -> list[McpImage | str]:
    """Like preview_video, with a semi-transparent grid (default 10x10) drawn on every frame to anchor positions."""
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
    grid = GridOptions(
        columns=columns,
        rows=rows,
        mode=mode,
        column_width=column_width,
        row_width=row_width,
        color=color,
        opacity=opacity,
        line_width=line_width,
    )
    return _render_frames(options, fps, start, end, max_frames, grid)
