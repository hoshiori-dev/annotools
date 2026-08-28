"""Internal: PyAV import guard and fsspec-backed container opening shared by ``video`` and ``audio``."""

from contextlib import ExitStack
from typing import Any

import fsspec


def require_av(feature: str) -> Any:
    """Import and return PyAV, or raise ``ImportError`` naming the extra that provides it."""
    try:
        import av
    except ImportError as exc:
        raise ImportError(f"{feature} support requires PyAV: install annotools[media]") from exc
    return av


def open_container(av: Any, uri: str, stack: ExitStack) -> Any:
    """Open ``uri`` with PyAV through a streamed fsspec handle; every error names the URI.

    Raises:
        FileNotFoundError: when the source does not exist.
        OSError: for any other backend failure while opening the source.
        ValueError: when the content is not a decodable media file.
    """
    try:
        handle = stack.enter_context(fsspec.open(uri, "rb"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"cannot read {uri}: not found") from exc
    except Exception as exc:  # backend-specific errors share no base class
        raise OSError(f"cannot read {uri}: {exc}") from exc
    try:
        return stack.enter_context(av.open(handle))
    except Exception as exc:
        raise ValueError(f"{uri}: not a decodable media file ({exc})") from exc
