"""Composition root: the FastMCP instance with every tool module registered.

Importing this module registers all tools. The instance itself lives in ``annotools.mcp.app``.
"""

from annotools.mcp import audio, color, geometry, image, video  # noqa: F401
from annotools.mcp.app import mcp

__all__ = ["mcp"]
