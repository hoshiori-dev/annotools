"""FastMCP server definition. Tools are registered by the modules under ``annotools.tools``."""

from fastmcp import FastMCP

INSTRUCTIONS = (
    "Preview and overlay tools for annotating images, video, and audio within an MLLM token budget. "
    "All coordinates are normalized to 0.0-1.0 relative to the uncropped source."
)

mcp = FastMCP("annotools", instructions=INSTRUCTIONS)


def register_tools() -> None:
    """Import the tool modules so their ``@mcp.tool`` decorators run."""
    import annotools.tools.color_tools
    import annotools.tools.image_tools  # noqa: F401


register_tools()
