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


@tool("look_at_item", "Preview an item from the workspace (optional normalized crop and 10x10 grid)", {"uri": str})
async def look_at_item(args: dict[str, Any]) -> dict[str, Any]:
    try:
        data, meta = vision.look_at_item(args["uri"], crop=args.get("crop"), grid=args.get("grid"))
    except (ValueError, OSError) as exc:
        return {"content": [{"type": "text", "text": str(exc)}], "is_error": True}
    return image_result(data, meta)


@tool(
    "look_at_annotations",
    "Overlay candidate boxes (normalized xyxy) on an item with the grid so you can check them",
    {"uri": str, "bboxes": list},
)
async def look_at_annotations(args: dict[str, Any]) -> dict[str, Any]:
    try:
        data, meta = vision.look_at_annotations(args["uri"], bboxes=args["bboxes"], crop=args.get("crop"))
    except (ValueError, OSError) as exc:
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
