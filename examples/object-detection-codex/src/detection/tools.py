"""Execution-agent tools served over MCP (stdio) to the Codex thread: gridded preview, indexed overlay, commit.

Run as a server:
    python -m detection.tools --workspace <dir> --db <file> --run-id <n> --config <json> [--trial-dir <dir>]
"""

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

from annotools.image.grid import GridOptions, draw_grid
from annotools.image.overlay import BBoxObject, draw_bboxes
from annotools.image.preview import encode, preview
from annotools.io import load_image, write_bytes
from fastmcp import FastMCP
from fastmcp.utilities.types import Image as McpImage

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


def build_server(ctx: ToolContext) -> FastMCP:
    """Create the FastMCP server with the three tools bound to ``ctx``."""
    mcp = FastMCP("detection")

    @mcp.tool(output_schema=None)
    def look_at_item(uri: str) -> list:
        """Show the item with the grid; returns the image and its metadata (shown size, grid cell size)."""
        data, meta = ctx.look_at_item(uri)
        return [McpImage(data=data, format=meta["format"]), json.dumps(meta)]

    @mcp.tool(output_schema=None)
    def propose_boxes(uri: str, boxes: list[dict]) -> list:
        """Draw candidate boxes ({label, box: [x_min, y_min, x_max, y_max] in 0..999 space, confidence}), indexed."""
        data, meta = ctx.propose_boxes(uri, boxes)
        return [McpImage(data=data, format=meta["format"]), json.dumps(meta)]

    @mcp.tool
    def commit_boxes(uri: str, boxes: list[dict], done: bool) -> dict:
        """Store the final boxes (same shape); done=true if the last overlay was correct. An empty list means no cat."""
        try:
            return ctx.commit_boxes(uri, boxes, done)
        except sqlite3.Error as exc:
            raise ValueError(f"store error: {exc}") from exc

    return mcp


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Serve the detection tools over stdio.")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--config", required=True, help="JSON of config/default.json")
    parser.add_argument("--trial-dir", default=None)
    args = parser.parse_args(argv)
    ctx = ToolContext(Path(args.workspace), Path(args.db), args.run_id, json.loads(args.config))
    if args.trial_dir:
        ctx.trial_dir = Path(args.trial_dir)
        ctx.trial_dir.mkdir(parents=True, exist_ok=True)
    build_server(ctx).run()


if __name__ == "__main__":
    main()
