"""FastMCP server definition. Tools are registered by the modules under ``annotools.tools``."""

from fastmcp import FastMCP

INSTRUCTIONS = (
    "Preview and overlay tools for annotating images, video, and audio within an MLLM token budget. "
    "All coordinates are normalized to 0.0-1.0 relative to the uncropped source. Ask a model for coordinates in "
    "its native convention (pixels of the shown image, or a 0-1000 space) and convert with normalize_coordinates."
)

mcp = FastMCP("annotools", instructions=INSTRUCTIONS)


def register_tools() -> None:
    """Import the tool modules so their ``@mcp.tool`` decorators run."""
    from annotools.tools import audio_tools, color_tools, geometry_tools, image_tools, video_tools  # noqa: F401


register_tools()
