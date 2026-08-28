"""Reading and writing media through fsspec so local paths and remote URLs behave the same."""

import io

import fsspec
from PIL import Image, ImageOps, UnidentifiedImageError

__all__ = [
    "load_image",
    "open_bytes",
    "write_bytes",
]


def open_bytes(uri: str) -> bytes:
    r"""Read the full content of a local path or fsspec URL.

    Every source goes through fsspec so ``s3://``, ``gs://``, ``https://`` and plain paths behave the
    same; remote protocols need the matching backend from ``annotools[remote]``.

    Args:
        uri: Local path or fsspec URL.

    Returns:
        The raw bytes of the object.

    Raises:
        FileNotFoundError: When the URI does not exist; the message names the URI.
        OSError: For any other read failure (permissions, directory, unknown protocol, missing fsspec
            backend such as ``s3fs``, missing cloud credentials), with the URI and the reason in the message.

    Example:
        >>> from annotools import open_bytes
        >>> open_bytes("s3://bucket/photo.jpg")[:2]  # doctest: +SKIP
        b'\xff\xd8'
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

    Args:
        uri: Destination path or fsspec URL.
        data: Bytes to write (an encoded preview, a WAV clip).

    Raises:
        OSError: Naming the target URI when it cannot be written.

    Example:
        >>> from annotools import write_bytes
        >>> write_bytes("/tmp/previews/frame.jpg", b"...")  # doctest: +SKIP
    """
    try:
        with fsspec.open(uri, "wb", auto_mkdir=True) as fh:
            fh.write(data)
    except Exception as exc:  # same reasoning as open_bytes: backend errors share no base class
        raise OSError(f"cannot write {uri}: {exc}") from exc


def load_image(uri: str) -> Image.Image:
    """Decode an image from ``uri`` with EXIF orientation applied.

    Applying the orientation here means every later coordinate refers to the image as a viewer (and
    an MLLM) sees it, not to the sensor layout stored in the file.

    Args:
        uri: Local path or fsspec URL of an image Pillow can decode.

    Returns:
        The decoded, orientation-corrected PIL image (mode as stored: RGB, RGBA, L, P, ...).

    Raises:
        FileNotFoundError: When the URI does not exist (from :func:`open_bytes`).
        OSError: For other read failures (from :func:`open_bytes`).
        ValueError: When the content is not a decodable image (unknown format, truncated or corrupt
            data); the message names the URI.

    Example:
        >>> from annotools import load_image
        >>> load_image("data/raw/000000001675.jpg").size  # doctest: +SKIP
        (640, 480)
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
