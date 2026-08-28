"""Crop and resize a source image into a token-bounded preview."""

import io
from dataclasses import dataclass, field
from typing import Any

from PIL import Image

from annotools.config import get_settings
from annotools.geometry import FULL_FRAME, Box, fit_size, normalized_box_to_pixels, validate_normalized_box

__all__ = [
    "PreviewResult",
    "encode",
    "preview",
]

FORMATS = {"jpeg": "JPEG", "png": "PNG", "webp": "WEBP"}
MIME_TYPES = {"jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}


@dataclass
class PreviewResult:
    """A rendered preview plus the metadata agents need to map it back to the source."""

    image: Image.Image
    metadata: dict[str, Any] = field(default_factory=dict)
    crop_pixels: tuple[int, int, int, int] | None = None
    """The applied crop in source pixels (None = full frame); exact, unlike re-deriving it from ``crop``."""


def preview(
    image: Image.Image,
    *,
    crop: Box | None = None,
    target_pixels: int | None = None,
    max_width: int | None = None,
    max_height: int | None = None,
    allow_upscale: bool = False,
) -> PreviewResult:
    """Crop ``image`` to the normalized ``crop`` box and fit it inside the size limits.

    Raises:
        ValueError: for an invalid ``crop`` or a limit smaller than 1.
    """
    settings = get_settings()
    max_width = settings.max_width if max_width is None else max_width
    max_height = settings.max_height if max_height is None else max_height
    original_size = image.size
    box = validate_normalized_box(crop, name="crop") if crop is not None else FULL_FRAME
    px_box: tuple[int, int, int, int] | None = None
    if box != FULL_FRAME:
        px_box = normalized_box_to_pixels(box, *original_size)
        image = image.crop(px_box)
        # Report the box that was actually applied (rounded outward to whole source pixels).
        width, height = original_size
        box = (px_box[0] / width, px_box[1] / height, px_box[2] / width, px_box[3] / height)
    cropped_size = image.size
    out_size = fit_size(
        *cropped_size,
        max_width=max_width,
        max_height=max_height,
        target_pixels=target_pixels,
        allow_upscale=allow_upscale,
    )
    if out_size != cropped_size:
        resample = Image.Resampling.LANCZOS if out_size[0] < cropped_size[0] else Image.Resampling.BICUBIC
        image = image.resize(out_size, resample)
    metadata = size_metadata(original_size, box, out_size, out_size[0] / cropped_size[0])
    return PreviewResult(image=image, metadata=metadata, crop_pixels=px_box)


def size_metadata(
    original_size: tuple[int, int], crop: Box, output_size: tuple[int, int], scale: float
) -> dict[str, Any]:
    """Build the base metadata every preview carries: sizes as ``[w, h]`` pairs and as scalar keys.

    The scalar keys (``original_width``, ``output_width``, …) repeat the pairs so a model can read them
    without indexing; ``scale`` is output pixels per source pixel of the cropped view.
    """
    return {
        "original_size": list(original_size),
        "original_width": original_size[0],
        "original_height": original_size[1],
        "crop": [_num(v) for v in crop],
        "output_size": list(output_size),
        "output_width": output_size[0],
        "output_height": output_size[1],
        "scale": scale,
    }


def encode(image: Image.Image, output_format: str | None = None) -> bytes:
    """Encode ``image`` as ``jpeg`` (quality from config, alpha flattened on white), ``png``, or ``webp``.

    Raises:
        ValueError: for an unknown ``output_format``.
    """
    settings = get_settings()
    output_format = settings.output_format if output_format is None else output_format
    if output_format not in FORMATS:
        raise ValueError(f"output_format must be one of {sorted(FORMATS)}, got {output_format!r}")
    if output_format == "jpeg" and image.mode not in ("RGB", "L"):
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, "white")
        image = Image.alpha_composite(background, rgba).convert("RGB")
    buffer = io.BytesIO()
    kwargs: dict[str, Any] = {"quality": settings.jpeg_quality} if output_format == "jpeg" else {}
    image.save(buffer, format=FORMATS[output_format], **kwargs)
    return buffer.getvalue()


def _num(value: float) -> float | int:
    return int(value) if float(value).is_integer() else value
