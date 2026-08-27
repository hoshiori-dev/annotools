"""Reading and writing media through fsspec so local paths and remote URLs behave the same."""

import io

import fsspec
from PIL import Image, ImageOps


def open_bytes(uri: str) -> bytes:
    """Read the full content of a local path or fsspec URL.

    Raises:
        FileNotFoundError: when the URI cannot be opened; the message names the URI.
    """
    try:
        with fsspec.open(uri, "rb") as fh:
            return fh.read()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"cannot read {uri}") from exc


def write_bytes(uri: str, data: bytes) -> None:
    """Write bytes to a local path or fsspec URL, creating parent directories for local paths."""
    with fsspec.open(uri, "wb", auto_mkdir=True) as fh:
        fh.write(data)


def load_image(uri: str) -> Image.Image:
    """Decode an image from ``uri`` with EXIF orientation applied."""
    image = Image.open(io.BytesIO(open_bytes(uri)))
    image.load()
    return ImageOps.exif_transpose(image) or image
