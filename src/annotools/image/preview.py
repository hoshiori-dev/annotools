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


@dataclass
class PreviewResult:
    """A rendered preview plus the metadata agents need to map it back to the source.

    Attributes:
        image: The rendered PIL image (what the model will see).
        metadata: ``original_size`` / ``original_width`` / ``original_height``, the applied ``crop``
            (normalized), ``output_size`` / ``output_width`` / ``output_height``, and ``scale`` (output
            pixels per source pixel of the cropped view); overlays add their own keys (``grid``,
            ``objects``, ``ids``, ``legend``, ``image_size``).
        crop_pixels: The applied crop in source pixels (``None`` = full frame); exact, unlike
            re-deriving it from ``crop``.

    Examples:
        >>> from PIL import Image
        >>> from annotools import preview
        >>> preview(Image.new("RGB", (1600, 1200)), max_width=384, max_height=384).metadata[
        ...     "output_size"
        ... ]
        [384, 288]
    """

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
    """Crop ``image`` to a normalized box and shrink it to fit a token budget.

    The result is what an MLLM will see: agents localize on this view, so the returned metadata carries
    everything needed to map their answers back to the uncropped source (see
    :func:`annotools.normalize_coordinates`). Downscaling uses LANCZOS; upscaling (only with
    ``allow_upscale``) uses BICUBIC. EXIF orientation must already be applied (:func:`load_image` does).

    Args:
        image: Source image; not modified.
        crop: ``(x_min, y_min, x_max, y_max)`` normalized to [0, 1] relative to ``image``; ``None``
            keeps the full frame. The applied crop is rounded outward to whole pixels and reported back.
        target_pixels: Cap on the output area in pixels; combined with the size limits (smallest wins).
        max_width: Maximum output width in pixels; ``None`` uses ``Settings.max_width`` (384).
        max_height: Maximum output height in pixels; ``None`` uses ``Settings.max_height`` (384).
        allow_upscale: Enlarge small images or crops up to the limits instead of returning them as is.

    Returns:
        A :class:`PreviewResult` whose ``metadata`` has ``original_size`` / ``original_width`` /
        ``original_height``, the applied ``crop``, ``output_size`` / ``output_width`` /
        ``output_height``, and ``scale``; ``crop_pixels`` holds the exact source-pixel crop or ``None``.

    Raises:
        ValueError: ``crop`` has a value outside [0, 1] or ``min >= max`` (message starts with
            ``crop:``), or a limit is smaller than 1.

    Examples:
        >>> from PIL import Image
        >>> from annotools import preview
        >>> result = preview(
        ...     Image.new("RGB", (1600, 1200)),
        ...     crop=(0.5, 0.5, 1.0, 1.0),
        ...     max_width=384,
        ...     max_height=384,
        ... )
        >>> result.image.size, result.metadata["scale"]
        ((384, 288), 0.48)

    References:
        - Spec: ``.agents/knowledge/spec/preview-image.md`` and ``mcp-overview.md`` (annotools repository).
        - Default 384 px: the largest size Gemini bills as one 258-token unit,
          https://ai.google.dev/gemini-api/docs/image-understanding (verified 2026-08-27); Claude and GPT
          bill by area, so pass larger limits for them (``ARCHITECTURE.md``, Decisions).
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
    """Build the base metadata every preview carries: sizes as ``[w, h]`` pairs and as scalar keys."""
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
    r"""Encode ``image`` as ``jpeg``, ``png``, or ``webp`` bytes.

    JPEG is the default because it is the cheapest to send; alpha is flattened onto white for JPEG and
    the quality comes from ``Settings.jpeg_quality`` (90).

    Args:
        image: The image to encode (any mode; converted as the format requires).
        output_format: ``"jpeg"``, ``"png"``, or ``"webp"``; ``None`` uses ``Settings.output_format``.

    Returns:
        The encoded bytes.

    Raises:
        ValueError: For an unknown ``output_format``.

    Examples:
        >>> from PIL import Image
        >>> from annotools import encode
        >>> encode(Image.new("RGB", (10, 10)), "png")[:4]
        b'\x89PNG'

    References:
        - Spec: ``.agents/knowledge/spec/mcp-overview.md`` (annotools repository), ``output_format``.
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
