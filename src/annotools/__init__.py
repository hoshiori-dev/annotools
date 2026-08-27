"""annotools: MCP server and library that help agents view multimodal data within a token budget."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("annotools")
except PackageNotFoundError:  # pragma: no cover - only when running from an unbuilt checkout
    __version__ = "0.0.0"

__all__ = ["__version__"]
