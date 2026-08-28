"""The FastMCP application instance.

This module imports no tool module so that the tool modules can import ``mcp`` from here without
creating an import cycle. ``annotools.mcp.server`` is the composition root that loads the tools.
"""

from fastmcp import FastMCP

INSTRUCTIONS = (
    "Preview and overlay tools for annotating images, video, and audio within an MLLM token budget. "
    "All coordinates are normalized to 0.0-1.0 relative to the uncropped source. Ask a model for coordinates in "
    "its native convention (pixels of the shown image, or a 0-1000 space) and convert with normalize_coordinates."
)

mcp = FastMCP("annotools", instructions=INSTRUCTIONS)
