"""Composition root: the FastMCP instance with every tool module registered.

Importing this module registers all tools. The instance itself lives in ``annotools.app``.
"""

from annotools.app import mcp
from annotools.tools import audio_tools, color_tools, geometry_tools, image_tools, video_tools  # noqa: F401

__all__ = ["mcp"]
