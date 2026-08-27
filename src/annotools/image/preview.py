"""Crop and resize a source image into a token-bounded preview."""

import io
from dataclasses import dataclass, field
from typing import Any

from PIL import Image

from annotools import config
from annotools.geometry import FULL_FRAME, Box, fit_size, normalized_box_to_pixels, validate_normalized_box

FORMATS = {"jpeg": "JPEG", "png": "PNG", "webp": "WEBP"}
MIME_TYPES = {"jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}


@dataclass
class PreviewResult:
    """A rendered preview plus the metadata agents need to map it back to the source."""

    image: Image.Image
    metadata: dict[str, Any] = field(default_factory=dict)


def preview(
    image: Image.Image,
    *,
    crop: Box | None = None,
    target_pixels: int | None = None,
    max_width: int = config.MAX_PREVIEW_WIDTH,
    max_height: int = config.MAX_PREVIEW_HEIGHT,
    allow_upscale: bool = False,
) -> PreviewResult:
    """Crop ``image`` to the normalized ``crop`` box and fit it inside the size limits.

    Raises:
        ValueError: for an invalid ``crop`` or a limit smaller than 1.
    """
    original_size = image.size
    box = validate_normalized_box(crop, name="crop") if crop is not None else FULL_FRAME
    if box != FULL_FRAME:
        image = image.crop(normalized_box_to_pixels(box, *original_size))
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
    metadata = {
        "original_size": list(original_size),
        "crop": [_num(v) for v in box],
        "output_size": list(out_size),
        "scale": out_size[0] / cropped_size[0],
    }
    return PreviewResult(image=image, metadata=metadata)


def encode(image: Image.Image, output_format: str = config.DEFAULT_OUTPUT_FORMAT) -> bytes:
    """Encode ``image`` as ``jpeg`` (quality from config, alpha flattened on white), ``png``, or ``webp``.

    Raises:
        ValueError: for an unknown ``output_format``.
    """
    if output_format not in FORMATS:
        raise ValueError(f"output_format must be one of {sorted(FORMATS)}, got {output_format!r}")
    if output_format == "jpeg" and image.mode != "RGB":
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, "white")
        image = Image.alpha_composite(background, rgba).convert("RGB")
    buffer = io.BytesIO()
    kwargs: dict[str, Any] = {"quality": config.JPEG_QUALITY} if output_format == "jpeg" else {}
    image.save(buffer, format=FORMATS[output_format], **kwargs)
    return buffer.getvalue()


def _num(value: float) -> float | int:
    return int(value) if float(value).is_integer() else value
