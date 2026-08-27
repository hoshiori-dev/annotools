"""Execution-agent tools: gridded preview, indexed overlay of candidate boxes, and the commit."""

import base64
import json
import sqlite3
from pathlib import Path
from typing import Any

from annotools.image.grid import GridOptions, draw_grid
from annotools.image.overlay import BBoxObject, draw_bboxes
from annotools.image.preview import encode, preview
from annotools.io import load_image, write_bytes
from claude_agent_sdk import ToolAnnotations, create_sdk_mcp_server, tool

from detection import store
from detection.geometry import clean


class ToolContext:
    """Workspace confinement, preview/grid settings, the current run, and per-item round bookkeeping."""

    def __init__(self, workspace: Path, db: Path, run_id: int, config: dict[str, Any]) -> None:
        self.workspace = workspace.resolve()
        self.db, self.run_id, self.config = db, run_id, config
        self.classes = set(config["classes"])
        self.rounds: dict[str, int] = {}
        self.trial_dir: Path | None = None

    def inside(self, uri: str) -> Path:
        path = (self.workspace / uri).resolve()
        if self.workspace not in path.parents:
            raise ValueError(f"{uri}: outside the workspace")
        return path

    def _preview(self, uri: str):
        cfg = self.config["preview"]
        return preview(load_image(str(self.inside(uri))), max_width=cfg["max_width"], max_height=cfg["max_height"])

    def _render(self, uri: str):
        result = self._preview(uri)
        gridded = draw_grid(result.image, GridOptions(**self.config["grid"]))
        result.image = gridded.image
        result.metadata.update(gridded.metadata)
        return result

    def _clean(self, boxes, meta):
        convention = self.config.get("coordinates", "pixels")
        return clean(boxes, meta, self.classes, self.config.get("max_boxes", 20), convention)

    def look_at_item(self, uri: str) -> tuple[bytes, dict[str, Any]]:
        result = self._render(uri)
        fmt = self.config["preview"].get("output_format", "jpeg")
        return encode(result.image, fmt), {**result.metadata, "format": fmt}

    def propose_boxes(self, uri: str, boxes: list[dict[str, Any]]) -> tuple[bytes, dict[str, Any]]:
        result = self._render(uri)
        kept, rejected = self._clean(boxes, result.metadata)
        self.rounds[uri] = self.rounds.get(uri, 0) + 1
        objects = [BBoxObject(bbox=tuple(b["bbox"]), label=f"{i}:{b['label']}") for i, b in enumerate(kept)]
        if objects:
            result = draw_bboxes(result, objects)
        fmt = self.config["preview"].get("output_format", "jpeg")
        data = encode(result.image, fmt)
        meta = {**result.metadata, "format": fmt, "round": self.rounds[uri], "kept": len(kept), "rejected": rejected}
        if self.trial_dir:
            write_bytes(str(self.trial_dir / f"{Path(uri).stem}_round{self.rounds[uri]}.{fmt}"), data)
        return data, meta

    def commit_boxes(self, uri: str, boxes: list[dict[str, Any]], done: bool) -> dict[str, Any]:
        """Store the final boxes for the item in this run, replacing anything committed earlier in the run."""
        result = self._preview(uri)  # metadata only; no grid needed
        kept, rejected = self._clean(boxes, result.metadata)
        rounds = self.rounds.get(uri, 0)
        floor = self.config["confidence_floor"]
        low = any(b["confidence"] < floor for b in kept)
        status = "needs_review" if not done or low else "final"
        with store.connect(self.db) as conn:
            item_id = store.item_id_for(conn, uri)
            if item_id is None:
                raise ValueError(f"{uri}: unknown item")
            conn.execute("DELETE FROM annotations WHERE item_id = ? AND run_id = ?", (item_id, self.run_id))
            if not kept:
                store.record(
                    conn, item_id, self.run_id, "tag", "detection", {"tags": ["no_object"]}, status, rounds=rounds
                )
            for index, b in enumerate(kept):
                store.record(
                    conn,
                    item_id,
                    self.run_id,
                    "bbox",
                    str(index),
                    {"bbox": b["bbox"]},
                    status,
                    label=b["label"],
                    confidence=b["confidence"],
                    rounds=rounds,
                )
        return {"stored": len(kept), "status": status, "rounds": rounds, "rejected": rejected}


def build_server(ctx: ToolContext):
    def error(exc: Exception) -> dict[str, Any]:
        return {"content": [{"type": "text", "text": f"error: {exc}"}], "is_error": True}

    def image_blocks(data: bytes, meta: dict[str, Any]) -> dict[str, Any]:
        mime = f"image/{meta['format']}" if meta["format"] != "jpeg" else "image/jpeg"
        image = {"type": "image", "data": base64.b64encode(data).decode("ascii"), "mimeType": mime}
        return {"content": [image, {"type": "text", "text": json.dumps(meta)}]}

    @tool(
        "look_at_item",
        "Show the item with the grid; returns the image and its shown size (output_width x output_height)",
        {"uri": str},
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def look_at_item(args: dict[str, Any]) -> dict[str, Any]:
        try:
            return image_blocks(*ctx.look_at_item(args["uri"]))
        except (ValueError, OSError) as exc:
            return error(exc)

    @tool(
        "propose_boxes",
        "Draw candidate boxes on the gridded item and return the overlay. boxes: list of "
        '{"label": class, "box": [x1, y1, x2, y2] in pixels of the shown image, "confidence": 0-1}; '
        "boxes are indexed in the overlay",
        {"uri": str, "boxes": list},
    )
    async def propose_boxes(args: dict[str, Any]) -> dict[str, Any]:
        try:
            return image_blocks(*ctx.propose_boxes(args["uri"], list(args["boxes"])))
        except (ValueError, OSError, TypeError) as exc:
            return error(exc)

    @tool(
        "commit_boxes",
        "Store the final boxes (same shape as propose_boxes). done=true if the last overlay was correct, "
        "false if you ran out of rounds. An empty list means no cat.",
        {"uri": str, "boxes": list, "done": bool},
    )
    async def commit_boxes(args: dict[str, Any]) -> dict[str, Any]:
        try:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(ctx.commit_boxes(args["uri"], list(args["boxes"]), bool(args["done"]))),
                    }
                ]
            }
        except (ValueError, OSError, TypeError, sqlite3.Error) as exc:
            return error(exc)

    return create_sdk_mcp_server(name="detection", version="1.0.0", tools=[look_at_item, propose_boxes, commit_boxes])
