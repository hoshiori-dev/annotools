"""Semi-transparent grid overlay that helps an MLLM anchor positions."""

import math
from typing import Literal

import numpy as np
from PIL import Image
from pydantic import BaseModel, Field, model_validator

from annotools import config
from annotools.image.preview import PreviewResult


class GridOptions(BaseModel):
    """Grid parameters shared by every tool that accepts ``grid`` (see .agents/knowledge/spec/mcp-overview.md)."""

    columns: int = Field(default=config.GRID_COLUMNS, ge=1, description="Cells per row (columns-1 vertical lines)")
    rows: int = Field(default=config.GRID_ROWS, ge=1, description="Cells per column (rows-1 horizontal lines)")
    mode: Literal["ratio", "fixed"] = Field(default="ratio", description="ratio: equal cells; fixed: cells of given px")
    column_width: int | None = Field(default=None, ge=1, description="Cell width in output px (fixed mode)")
    row_width: int | None = Field(default=None, ge=1, description="Cell height in output px (fixed mode)")
    color: Literal["white", "black", "invert"] = Field(default="white")
    opacity: float = Field(default=config.GRID_OPACITY, ge=0.0, le=1.0)
    line_width: int = Field(default=config.GRID_LINE_WIDTH, ge=1)

    @model_validator(mode="after")
    def _fixed_needs_widths(self) -> "GridOptions":
        if self.mode == "fixed" and (self.column_width is None or self.row_width is None):
            raise ValueError("column_width/row_width are required when mode='fixed'")
        return self


def line_positions(size: int, cells: int, cell_size: int | None, mode: str) -> tuple[list[int], int]:
    """Return the line coordinates (excluding borders) and the resulting cell count along one axis."""
    if mode == "fixed":
        assert cell_size is not None
        positions = list(range(cell_size, size, cell_size))
        return positions, math.ceil(size / cell_size)
    return [round(size * i / cells) for i in range(1, cells)], cells


def draw_grid(image: Image.Image, options: GridOptions) -> PreviewResult:
    """Blend grid lines onto ``image`` and return it with ``grid`` metadata.

    Raises:
        ValueError: via ``GridOptions`` validation for invalid parameters.
    """
    width, height = image.size
    xs, columns = line_positions(width, options.columns, options.column_width, options.mode)
    ys, rows = line_positions(height, options.rows, options.row_width, options.mode)
    if options.mode == "fixed" and options.column_width is not None and options.row_width is not None:
        step_x, step_y = options.column_width / width, options.row_width / height
    else:
        step_x, step_y = 1 / columns, 1 / rows
    grid_meta = {"columns": columns, "rows": rows, "step_x": step_x, "step_y": step_y}
    if options.opacity == 0 or (not xs and not ys):
        return PreviewResult(image=image, metadata={"grid": grid_meta})
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    mask = np.zeros((height, width), dtype=bool)
    lw = options.line_width
    for x in xs:  # a band exactly line_width px wide, centred on the line position
        start = max(0, math.floor(x - lw / 2 + 0.5))  # centred band; avoids banker's rounding
        mask[:, start : min(width, start + lw)] = True
    for y in ys:
        start = max(0, math.floor(y - lw / 2 + 0.5))
        mask[start : min(height, start + lw), :] = True
    fill = {"white": 255.0, "black": 0.0}
    target = 255.0 - rgb if options.color == "invert" else np.full_like(rgb, fill[options.color])
    blended = rgb.copy()
    blended[mask] = rgb[mask] * (1 - options.opacity) + target[mask] * options.opacity
    out = Image.fromarray(np.clip(np.rint(blended), 0, 255).astype(np.uint8), "RGB")
    if image.mode == "RGBA":
        out.putalpha(image.getchannel("A"))
    return PreviewResult(image=out, metadata={"grid": grid_meta})
