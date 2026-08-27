"""Reading and writing media through fsspec so local paths and remote URLs behave the same."""

import io

import fsspec
from PIL import Image, ImageOps, UnidentifiedImageError


def open_bytes(uri: str) -> bytes:
    """Read the full content of a local path or fsspec URL.

    Raises:
        FileNotFoundError: when the URI does not exist; the message names the URI.
        OSError: for any other read failure (permissions, directory, unknown protocol, missing fsspec
            backend such as ``s3fs``, missing cloud credentials), with the URI and the reason in the message.
    """
    try:
        with fsspec.open(uri, "rb") as fh:
            return fh.read()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"cannot read {uri}: not found") from exc
    except Exception as exc:  # backend-specific errors (botocore, gcsfs, aiohttp) share no base class
        raise OSError(f"cannot read {uri}: {exc}") from exc


def write_bytes(uri: str, data: bytes) -> None:
    """Write bytes to a local path or fsspec URL, creating parent directories for local paths.

    Raises:
        OSError: naming the target URI when it cannot be written.
    """
    try:
        with fsspec.open(uri, "wb", auto_mkdir=True) as fh:
            fh.write(data)
    except Exception as exc:  # same reasoning as open_bytes: backend errors share no base class
        raise OSError(f"cannot write {uri}: {exc}") from exc


def load_image(uri: str) -> Image.Image:
    """Decode an image from ``uri`` with EXIF orientation applied.

    Raises:
        ValueError: when the content is not a decodable image (unknown format, truncated or corrupt
            data); the message names the URI.
    """
    data = open_bytes(uri)
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except UnidentifiedImageError as exc:
        raise ValueError(f"{uri}: not a decodable image") from exc
    except OSError as exc:  # Pillow reports truncated/corrupt files as OSError
        raise ValueError(f"{uri}: not a decodable image ({exc})") from exc
    return ImageOps.exif_transpose(image) or image
