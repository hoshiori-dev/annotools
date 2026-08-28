"""ID-mask overlays for instance, panoptic, and semantic segmentation previews."""

import math
from typing import Any, Literal

import numpy as np
from PIL import Image, ImageDraw

from annotools.color import color_from_text, to_hex
from annotools.config import get_settings
from annotools.geometry import fit_size
from annotools.image._draw import draw_label
from annotools.image.preview import PreviewResult, size_metadata
from annotools.io import load_image

__all__ = [
    "MASK_MODES",
    "load_mask",
    "overlay_mask",
]

# Keep in step with .agents/knowledge/spec/preview-image-segmentation.md.
MASK_MODES = {"L", "P", "I", "I;16", "I;16B", "I;16L"}


def load_mask(uri: str) -> np.ndarray:
    """Load a single-channel ID mask (0 = background) as an integer array.

    Masks are exchanged as ID images rather than color images so instance, panoptic, and semantic
    outputs share one contract (``ARCHITECTURE.md``, Decisions); the accepted modes are ``MASK_MODES``.

    Args:
        uri: Local path or fsspec URL of an ``L``, ``P``, ``I``, or ``I;16`` image.

    Returns:
        A 2-D ``int64`` array of IDs, the size of the mask image.

    Raises:
        ValueError: Naming ``mask_source`` when the image is not single-channel.
        FileNotFoundError: When the URI does not exist (from :func:`load_image`).

    Example:
        >>> from annotools import load_mask
        >>> load_mask("masks/000000001675.png").max()  # doctest: +SKIP
        3

    References:
        - Spec: ``.agents/knowledge/spec/preview-image-segmentation.md`` (annotools repository).
    """
    image = load_image(uri)
    if image.mode not in MASK_MODES:
        raise ValueError(
            f"mask_source: {uri} must be a single-channel ID image (L, P, I, or I;16), got mode {image.mode!r}"
        )
    return np.asarray(image).astype(np.int64)


def _resize_ids(mask: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    """Nearest-neighbour resize of an integer mask to ``(width, height)``."""
    if mask.shape[1] == size[0] and mask.shape[0] == size[1]:
        return mask
    image = Image.fromarray(mask.astype(np.int32), mode="I")
    return np.asarray(image.resize(size, Image.Resampling.NEAREST)).astype(np.int64)


def _boundary(mask: np.ndarray) -> np.ndarray:
    edge = np.zeros(mask.shape, dtype=bool)
    edge[:, 1:] |= mask[:, 1:] != mask[:, :-1]
    edge[:, :-1] |= mask[:, 1:] != mask[:, :-1]
    edge[1:, :] |= mask[1:, :] != mask[:-1, :]
    edge[:-1, :] |= mask[1:, :] != mask[:-1, :]
    return edge & (mask > 0)


def _thicken(edge: np.ndarray, width: int) -> np.ndarray:
    out = edge.copy()
    for _ in range(width - 1):
        grown = out.copy()
        grown[1:, :] |= out[:-1, :]
        grown[:-1, :] |= out[1:, :]
        grown[:, 1:] |= out[:, :-1]
        grown[:, :-1] |= out[:, 1:]
        out = grown
    return out


def _legend_strip(entries: list[dict[str, Any]], width: int) -> Image.Image:
    row_h, swatch, pad = 18, 12, 6
    col_w = max(120, min(width, 220))
    cols = max(1, width // col_w)
    rows = math.ceil(len(entries) / cols)
    strip = Image.new("RGB", (width, rows * row_h + pad), "white")
    draw = ImageDraw.Draw(strip)
    for i, entry in enumerate(entries):
        x = (i % cols) * col_w + pad
        y = (i // cols) * row_h + pad // 2
        color = tuple(int(entry["color"][j : j + 2], 16) for j in (1, 3, 5))
        draw.rectangle((x, y + 3, x + swatch, y + 3 + swatch), fill=color)
        draw.text((x + swatch + 4, y), f"{entry['id']}  {entry['name']}", fill="black")
    return strip


def overlay_mask(
    result: PreviewResult,
    mask: np.ndarray,
    *,
    annotation: Literal["label", "legend"] | str = "label",
    id_names: dict[int, str] | None = None,
    alpha: float = 0.5,
    line_width: int | None = None,
    max_width: int | None = None,
    max_height: int | None = None,
    target_pixels: int | None = None,
) -> PreviewResult:
    """Blend the ID ``mask`` over ``result.image`` and annotate regions with labels or a legend.

    ``mask`` is in source pixel space (any size; resized to the source with nearest neighbour), then
    follows the preview's crop and scale. Each ID gets a stable color from :func:`color_from_text`, so
    the same instance keeps its color across previews. ``annotation="legend"`` appends a color strip
    below the image and re-fits the composite to the size limits.

    Args:
        result: A preview from :func:`preview`; not modified (a new image is returned).
        mask: 2-D integer array of IDs, 0 = background (from :func:`load_mask`).
        annotation: ``"label"`` draws each ID's name at the region centre; ``"legend"`` lists IDs and
            colors in a strip and in ``metadata["legend"]``.
        id_names: Optional ``{id: name}`` for labels and legend entries; missing IDs use the number.
        alpha: Blend strength of the region color in [0, 1].
        line_width: Boundary width in output pixels (0 = no boundary); ``None`` uses
            ``Settings.line_width``.
        max_width: Size limit for the legend composite; ``None`` uses ``Settings.max_width``.
        max_height: Likewise; ``None`` uses ``Settings.max_height``.
        target_pixels: Optional area cap for the legend composite.

    Returns:
        A new :class:`PreviewResult` with ``metadata["ids"]`` (count of visible IDs) and, for the
        legend, ``metadata["legend"]``, ``image_size`` (the area the inverse mapping applies to) and
        refreshed size keys.

    Raises:
        ValueError: For ``alpha`` outside [0, 1], ``line_width < 0``, or an unknown ``annotation``.

    Example:
        >>> import numpy as np
        >>> from PIL import Image
        >>> from annotools import overlay_mask, preview
        >>> result = preview(
        ...     Image.new("RGB", (100, 100), "white"), max_width=100, max_height=100
        ... )
        >>> mask = np.zeros((100, 100), dtype=np.uint8)
        >>> mask[20:60, 20:60] = 1
        >>> overlay_mask(result, mask).metadata["ids"]
        1

    References:
        - Spec: ``.agents/knowledge/spec/preview-image-segmentation.md`` (annotools repository).
    """
    settings = get_settings()
    line_width = settings.line_width if line_width is None else line_width
    max_width = settings.max_width if max_width is None else max_width
    max_height = settings.max_height if max_height is None else max_height
    if not 0.0 <= alpha <= 1.0:
        raise ValueError(f"alpha must be within [0, 1], got {alpha}")
    if line_width < 0:
        raise ValueError(f"line_width must be >= 0, got {line_width}")
    if annotation not in ("label", "legend"):
        raise ValueError(f"annotation must be 'label' or 'legend', got {annotation!r}")
    names = {int(k): v for k, v in (id_names or {}).items()}
    original_w, original_h = result.metadata["original_size"]
    full = _resize_ids(mask, (original_w, original_h))
    x0, y0, x1, y1 = result.crop_pixels or (0, 0, original_w, original_h)
    cropped = full[y0:y1, x0:x1]
    view = _resize_ids(cropped, result.image.size)
    ids = [int(v) for v in np.unique(view) if v != 0]

    if result.image.mode == "RGBA":
        image = Image.alpha_composite(Image.new("RGBA", result.image.size, "white"), result.image).convert("RGB")
    else:
        image = result.image.convert("RGB")
    rgb = np.asarray(image, dtype=np.float32)
    colors = {i: color_from_text(str(i)) for i in ids}
    for i in ids:
        region = view == i
        rgb[region] = rgb[region] * (1 - alpha) + np.array(colors[i], dtype=np.float32) * alpha
    if line_width > 0:
        edges = _thicken(_boundary(view), line_width)
        for i in ids:
            sel = edges & (view == i)
            rgb[sel] = np.array(colors[i], dtype=np.float32)
    image = Image.fromarray(np.clip(np.rint(rgb), 0, 255).astype(np.uint8), "RGB")
    metadata: dict[str, Any] = {**result.metadata, "ids": len(ids)}

    if annotation == "label":
        draw = ImageDraw.Draw(image)
        for i in ids:
            ys, xs = np.nonzero(view == i)
            draw_label(
                draw, names.get(i, str(i)), float(xs.mean()), float(ys.mean()), colors[i], image.size, anchor="middle"
            )
    else:
        entries = [{"id": i, "name": names.get(i, str(i)), "color": to_hex(colors[i])} for i in ids]
        metadata["legend"] = entries
        strip = _legend_strip(entries, image.width)
        combined = Image.new("RGB", (image.width, image.height + strip.height), "white")
        combined.paste(image, (0, 0))
        combined.paste(strip, (0, image.height))
        size = fit_size(
            combined.width, combined.height, max_width=max_width, max_height=max_height, target_pixels=target_pixels
        )
        factor = size[0] / combined.width
        if size != combined.size:
            combined = combined.resize(size, Image.Resampling.LANCZOS)
        # output_size is the composite; image_size is the area the inverse mapping applies to.
        metadata.update(
            size_metadata((original_w, original_h), result.metadata["crop"], size, result.metadata["scale"] * factor)
        )
        metadata["image_size"] = [round(image.width * factor), round(image.height * factor)]
        if "grid" in metadata:  # the grid was drawn before the re-fit: its pixel cell sizes shrink with it
            metadata["grid"] = {
                **metadata["grid"],
                "cell_width": metadata["grid"]["cell_width"] * factor,
                "cell_height": metadata["grid"]["cell_height"] * factor,
            }
        image = combined
    return PreviewResult(image=image, metadata=metadata)
