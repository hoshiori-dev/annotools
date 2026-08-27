"""Claude Agent SDK wiring for the vision tools (copy into src/ and adjust paths).

Run: python claude_tools.py  (expects ANTHROPIC auth via the SDK's usual channels)
"""

import asyncio
import base64
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, create_sdk_mcp_server, query, tool

from vision_tools import VisionTools, metadata_text

WORKSPACE = "workspaces/coco-cats"
vision = VisionTools(WORKSPACE, max_width=768, max_height=768)


def image_result(data: bytes, meta: dict[str, Any], mime: str = "image/jpeg") -> dict[str, Any]:
    return {
        "content": [
            {"type": "image", "data": base64.b64encode(data).decode("ascii"), "mimeType": mime},
            {"type": "text", "text": metadata_text(meta)},
        ]
    }


@tool(
    "look_at_item",
    "Preview a workspace item. Optional: crop=[x_min, y_min, x_max, y_max] normalized 0-1; grid={} for the default "
    "10x10 grid or {\"columns\": n, \"rows\": m}.",
    {"uri": str},
)
async def look_at_item(args: dict[str, Any]) -> dict[str, Any]:
    grid = args.get("grid")
    if grid is not None and not isinstance(grid, dict):
        return {"content": [{"type": "text", "text": "grid must be an object such as {} or {\"columns\": 4}"}], "is_error": True}
    try:
        data, meta = vision.look_at_item(args["uri"], crop=args.get("crop"), grid=grid)
    except (ValueError, OSError, TypeError) as exc:
        return {"content": [{"type": "text", "text": str(exc)}], "is_error": True}
    return image_result(data, meta)


@tool(
    "look_at_annotations",
    "Overlay candidate boxes on an item with the grid so you can check them. bboxes is a list of objects "
    "{\"bbox\": [x_min, y_min, x_max, y_max] normalized 0-1, \"label\": str}; optional crop as in look_at_item.",
    {"uri": str, "bboxes": list},
)
async def look_at_annotations(args: dict[str, Any]) -> dict[str, Any]:
    try:
        data, meta = vision.look_at_annotations(args["uri"], bboxes=args["bboxes"], crop=args.get("crop"))
    except (ValueError, OSError, TypeError) as exc:
        return {"content": [{"type": "text", "text": str(exc)}], "is_error": True}
    return image_result(data, meta)


server = create_sdk_mcp_server(name="vision", version="1.0.0", tools=[look_at_item, look_at_annotations])


async def main() -> None:
    options = ClaudeAgentOptions(
        cwd=WORKSPACE,
        tools=[],  # no built-in file/shell tools for the execution agent
        mcp_servers={"vision": server},
        allowed_tools=["mcp__vision__*"],
        permission_mode="dontAsk",
    )
    async for message in query(prompt="Look at data/raw/000001.jpg and list the cats you see.", options=options):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            print(message.result)


if __name__ == "__main__":
    asyncio.run(main())
