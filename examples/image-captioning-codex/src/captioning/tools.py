"""Execution-agent tools served over MCP (stdio) to the Codex thread: look at an item, record captions and tags.

Run as a server: python -m captioning.tools --workspace <dir> --db <file> --run-id <n> --preview <json>
"""

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

from annotools.image.preview import encode, preview
from annotools.io import load_image
from fastmcp import FastMCP
from fastmcp.utilities.types import Image as McpImage

from captioning import store


class ToolContext:
    """State shared by the tools: workspace confinement, preview size, and the current run."""

    def __init__(self, workspace: Path, db: Path, run_id: int, preview_cfg: dict[str, Any]) -> None:
        self.workspace = workspace.resolve()
        self.db, self.run_id, self.preview_cfg = db, run_id, preview_cfg

    def inside(self, uri: str) -> Path:
        path = (self.workspace / uri).resolve()
        if self.workspace not in path.parents:
            raise ValueError(f"{uri}: outside the workspace")
        return path

    def look_at_item(self, uri: str) -> tuple[bytes, dict[str, Any]]:
        result = preview(
            load_image(str(self.inside(uri))),
            max_width=self.preview_cfg["max_width"],
            max_height=self.preview_cfg["max_height"],
        )
        fmt = self.preview_cfg.get("output_format", "jpeg")
        return encode(result.image, fmt), {**result.metadata, "format": fmt}

    def record_caption(self, uri: str, variant: str, text: str) -> dict[str, Any]:
        if variant not in store.VARIANT_KEYS:
            raise ValueError(f"variant must be one of {store.VARIANT_KEYS}, got {variant!r}")
        with store.connect(self.db) as conn:
            item_id = store.item_id_for(conn, uri)
            if item_id is None:
                raise ValueError(f"{uri}: unknown item")
            annotation_id = store.record(conn, item_id, self.run_id, "caption", variant, {"text": text.strip()})
        return {"annotation_id": annotation_id, "variant": variant, "words": len(text.split())}

    def record_tags(self, uri: str, tags: list[str]) -> dict[str, Any]:
        clean = sorted({t.strip().lower() for t in tags if t.strip()})
        if not 3 <= len(clean) <= 8:
            raise ValueError(f"expected 3-8 tags, got {len(clean)}")
        with store.connect(self.db) as conn:
            item_id = store.item_id_for(conn, uri)
            if item_id is None:
                raise ValueError(f"{uri}: unknown item")
            annotation_id = store.record(conn, item_id, self.run_id, "tag", "", {"tags": clean})
        return {"annotation_id": annotation_id, "tags": clean}


def build_server(ctx: ToolContext) -> FastMCP:
    """Create the FastMCP server with the three tools bound to ``ctx``."""
    mcp = FastMCP("captioning")

    @mcp.tool(output_schema=None)
    def look_at_item(uri: str) -> list:
        """Show the image for a workspace item at preview size; returns the image and its size metadata."""
        data, meta = ctx.look_at_item(uri)
        return [McpImage(data=data, format=meta["format"]), json.dumps(meta)]

    @mcp.tool
    def record_caption(uri: str, variant: str, text: str) -> dict:
        """Store one caption variant (long, medium, or short) for the item."""
        try:
            return ctx.record_caption(uri, variant, text)
        except sqlite3.Error as exc:
            raise ValueError(f"store error: {exc}") from exc

    @mcp.tool
    def record_tags(uri: str, tags: list[str]) -> dict:
        """Store the 3-8 tags for the item."""
        try:
            return ctx.record_tags(uri, tags)
        except sqlite3.Error as exc:
            raise ValueError(f"store error: {exc}") from exc

    return mcp


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Serve the captioning tools over stdio.")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--preview", default='{"max_width": 768, "max_height": 768, "output_format": "jpeg"}')
    args = parser.parse_args(argv)
    ctx = ToolContext(Path(args.workspace), Path(args.db), args.run_id, json.loads(args.preview))
    build_server(ctx).run()


if __name__ == "__main__":
    main()
