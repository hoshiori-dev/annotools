"""Reading and writing media through fsspec so local paths and remote URLs behave the same."""

import io

import fsspec
from PIL import Image, ImageOps, UnidentifiedImageError


def open_bytes(uri: str) -> bytes:
    """Read the full content of a local path or fsspec URL.

    Raises:
        FileNotFoundError: when the URI does not exist; the message names the URI.
        OSError: for any other read failure (permissions, directory, missing fsspec backend such as
            ``s3fs``), with the URI and the underlying reason in the message.
    """
    try:
        with fsspec.open(uri, "rb") as fh:
            return fh.read()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"cannot read {uri}: not found") from exc
    except (OSError, ImportError, ValueError) as exc:
        raise OSError(f"cannot read {uri}: {exc}") from exc


def write_bytes(uri: str, data: bytes) -> None:
    """Write bytes to a local path or fsspec URL, creating parent directories for local paths."""
    with fsspec.open(uri, "wb", auto_mkdir=True) as fh:
        fh.write(data)


def load_image(uri: str) -> Image.Image:
    """Decode an image from ``uri`` with EXIF orientation applied.

    Raises:
        ValueError: when the content is not a decodable image; the message names the URI.
    """
    try:
        image = Image.open(io.BytesIO(open_bytes(uri)))
        image.load()
    except UnidentifiedImageError as exc:
        raise ValueError(f"{uri}: not a decodable image") from exc
    return ImageOps.exif_transpose(image) or image
