"""Codex SDK wiring: expose the vision tools as a FastMCP stdio server the Codex thread loads.

Run the server:   python codex_tools.py serve --workspace workspaces/coco-cats
Use from Python:  see run_thread() below (openai-codex package).
"""

import base64
import json
import sys

from fastmcp import FastMCP
from fastmcp.utilities.types import Image

from vision_tools import VisionTools, metadata_text


def build_server(workspace: str) -> FastMCP:
    vision = VisionTools(workspace)
    mcp = FastMCP("vision")

    @mcp.tool(output_schema=None)
    def look_at_item(uri: str, crop: list[float] | None = None, grid: dict | None = None) -> list:
        """Preview a workspace item (optional normalized crop and grid)."""
        data, meta = vision.look_at_item(uri, crop=tuple(crop) if crop else None, grid=grid)
        return [Image(data=data, format="jpeg"), metadata_text(meta)]

    @mcp.tool(output_schema=None)
    def look_at_annotations(uri: str, bboxes: list[dict]) -> list:
        """Overlay candidate boxes (normalized xyxy) with the grid to check them."""
        data, meta = vision.look_at_annotations(uri, bboxes=bboxes)
        return [Image(data=data, format="jpeg"), metadata_text(meta)]

    return mcp


def run_thread(workspace: str, prompt: str) -> str:
    """Start a confined Codex thread with the vision MCP server registered through config."""
    from openai_codex import Codex, Sandbox  # pip install openai-codex

    config = {
        "mcp_servers": {"vision": {"command": sys.executable, "args": [__file__, "serve", "--workspace", workspace]}}
    }
    with Codex() as codex:
        thread = codex.thread_start(cwd=workspace, sandbox=Sandbox.workspace_write, config=config)
        result = thread.run(prompt)
    return result.final_response if hasattr(result, "final_response") else str(result)


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "serve":
        build_server(sys.argv[3]).run()
    else:
        print(json.dumps({"usage": "codex_tools.py serve --workspace <dir>"}))
        base64  # keep the import for wrappers that pack raw blocks
