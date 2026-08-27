"""SDK-independent core for execution-agent vision tools, built on the annotools library.

Every function takes a workspace-relative URI, refuses paths outside the workspace, and returns
(encoded_bytes, metadata) so an SDK wrapper only has to base64-encode and pack content blocks.
"""

import json
from pathlib import Path
from typing import Any

from annotools.image.grid import GridOptions, draw_grid
from annotools.image.overlay import BBoxObject, KeypointObject, PolygonObject, draw_bboxes, draw_keypoints, draw_polygons
from annotools.image.preview import encode, preview
from annotools.io import load_image


DEFAULT_GRID = object()  # sentinel: "draw the default grid"; an explicit None suppresses it


class VisionTools:
    """Preview and overlay helpers confined to one workspace."""

    def __init__(self, workspace: str | Path, max_width: int = 768, max_height: int = 768, output_format: str = "jpeg") -> None:
        self.workspace = Path(workspace).resolve()
        self.max_width, self.max_height, self.output_format = max_width, max_height, output_format

    def _inside(self, uri: str) -> Path:
        path = (self.workspace / uri).resolve() if not Path(uri).is_absolute() else Path(uri).resolve()
        if self.workspace not in path.parents and path != self.workspace:
            raise ValueError(f"{uri}: outside the workspace {self.workspace}")
        return path

    def _render(self, uri: str, crop, grid: dict[str, Any] | None):
        result = preview(load_image(str(self._inside(uri))), crop=crop, max_width=self.max_width, max_height=self.max_height)
        if grid is not None:
            gridded = draw_grid(result.image, GridOptions(**grid))
            result.image = gridded.image
            result.metadata.update(gridded.metadata)
        return result

    def look_at_item(self, uri: str, crop=None, grid: dict[str, Any] | None = None) -> tuple[bytes, dict[str, Any]]:
        """Preview an item (optionally cropped and gridded)."""
        result = self._render(uri, crop, grid)
        return encode(result.image, self.output_format), {**result.metadata, "format": self.output_format}

    def look_at_annotations(self, uri: str, bboxes=None, keypoints=None, polygons=None, crop=None, grid=DEFAULT_GRID):
        """Overlay the agent's candidate annotations (normalized to the uncropped source).

        ``bboxes``: ``[{"bbox": [x0, y0, x1, y1], "label"?: str, "color"?: str}]``; ``keypoints``:
        ``[{"point": [x, y], ...}]``; ``polygons``: ``[{"points": [x1, y1, ...], ...}]``. ``grid`` defaults to the
        10x10 grid the agent proposed on; pass ``None`` to suppress it.
        """
        result = self._render(uri, crop, {} if grid is DEFAULT_GRID else grid)
        counts = {}
        if bboxes:
            result = draw_bboxes(result, [BBoxObject(**b) for b in bboxes])
            counts["bboxes"] = len(bboxes)
        if keypoints:
            result = draw_keypoints(result, [KeypointObject(**k) for k in keypoints])
            counts["keypoints"] = len(keypoints)
        if polygons:
            result = draw_polygons(result, [PolygonObject(**p) for p in polygons])
            counts["polygons"] = len(polygons)
        meta = {k: v for k, v in result.metadata.items() if k != "objects"}
        return encode(result.image, self.output_format), {**meta, **counts, "format": self.output_format}


def metadata_text(meta: dict[str, Any]) -> str:
    """One-line JSON for the text block that accompanies every image."""
    return json.dumps(meta)
