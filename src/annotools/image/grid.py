"""Semi-transparent grid overlay that helps an MLLM anchor positions."""

import math
from typing import Literal

import numpy as np
from PIL import Image
from pydantic import BaseModel, Field

from annotools.config import get_settings
from annotools.image.preview import PreviewResult

__all__ = [
    "GridOptions",
    "draw_grid",
]


class GridOptions(BaseModel):
    """Grid parameters shared by every tool that accepts ``grid``.

    ``None`` fields take their value from :class:`~annotools.Settings` when the grid is drawn
    (:meth:`resolved`). A 10x10 ``ratio`` grid is the default because MLLMs anchor positions far better
    against visible cells than on a bare image, and 10 cells keep the labels legible at 384 px.

    Examples:
        >>> from annotools import GridOptions
        >>> GridOptions(columns=4).resolved().rows
        10

    References:
        - Spec: ``.agents/knowledge/spec/mcp-overview.md`` (annotools repository), ``GridOptions`` table.
    """

    columns: int | None = Field(
        default=None, ge=1, description="Cells per row (columns-1 vertical lines); null = setting (10)"
    )
    rows: int | None = Field(
        default=None, ge=1, description="Cells per column (rows-1 horizontal lines); null = setting (10)"
    )
    mode: Literal["ratio", "fixed"] | None = Field(
        default=None, description="ratio: equal cells; fixed: cells of given px; null = setting (ratio)"
    )
    column_width: int | None = Field(default=None, ge=1, description="Cell width in output px (fixed mode)")
    row_width: int | None = Field(default=None, ge=1, description="Cell height in output px (fixed mode)")
    color: Literal["white", "black", "invert"] = Field(
        default="white", description="Line color; invert flips the underlying pixels"
    )
    opacity: float | None = Field(default=None, ge=0.0, le=1.0, description="null = setting (0.5)")
    line_width: int | None = Field(default=None, ge=1, description="Output pixels; null = setting (1)")

    def resolved(self) -> "GridOptions":
        """Return a copy with every ``None`` filled from ``Settings``."""
        s = get_settings()
        out = self.model_copy(
            update={
                "columns": s.grid_columns if self.columns is None else self.columns,
                "rows": s.grid_rows if self.rows is None else self.rows,
                "mode": s.grid_mode if self.mode is None else self.mode,
                "column_width": s.grid_column_width if self.column_width is None else self.column_width,
                "row_width": s.grid_row_width if self.row_width is None else self.row_width,
                "opacity": s.grid_opacity if self.opacity is None else self.opacity,
                "line_width": s.grid_line_width if self.line_width is None else self.line_width,
            }
        )
        if out.mode == "fixed" and (out.column_width is None or out.row_width is None):
            raise ValueError("column_width/row_width are required when mode='fixed'")
        return out


def _line_positions(size: int, cells: int, cell_size: int | None, mode: str) -> tuple[list[int], int]:
    """Return the line coordinates (excluding borders) and the resulting cell count along one axis."""
    if mode == "fixed":
        assert cell_size is not None
        positions = list(range(cell_size, size, cell_size))
        return positions, math.ceil(size / cell_size)
    return [round(size * i / cells) for i in range(1, cells)], cells


def draw_grid(image: Image.Image, options: GridOptions) -> PreviewResult:
    """Blend grid lines onto ``image`` and return it with ``grid`` metadata.

    Lines are blended at ``options.opacity`` in white, black, or the inverted underlying pixels so the
    grid stays visible on any background without hiding it. Metadata reports the cell layout so
    coordinates can be reasoned about in cells and converted back.

    Args:
        image: The (already previewed) PIL image; RGBA input keeps its alpha channel.
        options: Grid layout; ``None`` fields resolve from ``Settings``.

    Returns:
        A :class:`PreviewResult` whose ``metadata["grid"]`` holds ``columns``, ``rows``, ``step_x`` /
        ``step_y`` (normalized cell step) and ``cell_width`` / ``cell_height`` (output pixels).

    Raises:
        ValueError: Via :meth:`GridOptions.resolved` when ``mode="fixed"`` has no cell widths.

    Examples:
        >>> from PIL import Image
        >>> from annotools import GridOptions, draw_grid
        >>> draw_grid(
        ...     Image.new("RGB", (200, 100)), GridOptions(columns=4, rows=2)
        ... ).metadata["grid"]["columns"]
        4

    References:
        - Spec: ``.agents/knowledge/spec/preview-image-grid.md`` (annotools repository).
    """
    options = options.resolved()
    assert options.columns is not None and options.rows is not None and options.mode is not None
    assert options.opacity is not None and options.line_width is not None
    width, height = image.size
    xs, columns = _line_positions(width, options.columns, options.column_width, options.mode)
    ys, rows = _line_positions(height, options.rows, options.row_width, options.mode)
    if options.mode == "fixed" and options.column_width is not None and options.row_width is not None:
        cell_w, cell_h = float(options.column_width), float(options.row_width)
        step_x, step_y = cell_w / width, cell_h / height
    else:
        step_x, step_y = 1 / columns, 1 / rows
        cell_w, cell_h = width / columns, height / rows
    grid_meta = {
        "columns": columns,
        "rows": rows,
        "step_x": step_x,
        "step_y": step_y,
        "cell_width": cell_w,
        "cell_height": cell_h,
    }
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
