"""Execution-agent tools: look at an item (annotools preview) and record caption variants (store)."""

import base64
import json
import sqlite3
from pathlib import Path
from typing import Any

from annotools.image.preview import encode, preview
from annotools.io import load_image
from claude_agent_sdk import ToolAnnotations, create_sdk_mcp_server, tool

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


def build_server(ctx: ToolContext):
    """Create the in-process MCP server with the three tools bound to ``ctx``."""

    def error(exc: Exception) -> dict[str, Any]:
        return {"content": [{"type": "text", "text": f"error: {exc}"}], "is_error": True}

    @tool(
        "look_at_item",
        "Show the image for a workspace item at preview size; returns the image and its size metadata",
        {"uri": str},
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def look_at_item(args: dict[str, Any]) -> dict[str, Any]:
        try:
            data, meta = ctx.look_at_item(args["uri"])
        except (ValueError, OSError) as exc:
            return error(exc)
        mime = "image/png" if meta["format"] == "png" else f"image/{meta['format']}"
        return {
            "content": [
                {"type": "image", "data": base64.b64encode(data).decode("ascii"), "mimeType": mime},
                {"type": "text", "text": json.dumps(meta)},
            ]
        }

    @tool(
        "record_caption",
        "Store one caption variant (long, medium, or short) for the item",
        {"uri": str, "variant": str, "text": str},
    )
    async def record_caption(args: dict[str, Any]) -> dict[str, Any]:
        try:
            return {
                "content": [
                    {"type": "text", "text": json.dumps(ctx.record_caption(args["uri"], args["variant"], args["text"]))}
                ]
            }
        except (ValueError, sqlite3.Error) as exc:
            return error(exc)

    @tool("record_tags", "Store the 3-8 tags for the item", {"uri": str, "tags": list})
    async def record_tags(args: dict[str, Any]) -> dict[str, Any]:
        try:
            return {"content": [{"type": "text", "text": json.dumps(ctx.record_tags(args["uri"], list(args["tags"])))}]}
        except (ValueError, sqlite3.Error) as exc:
            return error(exc)

    return create_sdk_mcp_server(name="captioning", version="1.0.0", tools=[look_at_item, record_caption, record_tags])
