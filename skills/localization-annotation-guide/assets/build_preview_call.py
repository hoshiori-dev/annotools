"""Turn model candidates into a preview_image_bboxes call and back.

Candidates arrive in the model's convention; this converts them to annotools' normalized xyxy using
the preview metadata returned by preview_image_grid, and builds the objects list with index labels.
"""

from typing import Any

from annotools.geometry import normalize_coordinates

# convention -> (base per axis: "pixels" uses the preview output size, a number is a fixed space; axis order)
CONVENTIONS: dict[str, tuple[str | float, str]] = {
    "pixels": ("pixels", "xy"),  # Claude, Qwen2.5-VL: pixels of the shown preview
    "thousand": (1000, "xy"),  # Qwen3-VL and any x-first 0-1000 space
    "gpt": (999, "xy"),  # GPT-5.4+ / Codex: fixed 0..999 space per the OpenAI vision tips
    "thousand_yx": (1000, "yx"),  # Gemini: [ymin, xmin, ymax, xmax] * 1000
    "gemini": (1000, "yx"),
}


def to_normalized(box: list[float], convention: str, meta: dict[str, Any]) -> list[float]:
    """Convert one candidate box to normalized xyxy relative to the uncropped source (clamped to 0-1).

    ``meta`` is the preview metadata (``output_width``/``output_height`` and the applied ``crop``).
    """
    if convention not in CONVENTIONS:
        raise ValueError(f"unknown convention {convention!r}; expected one of {sorted(CONVENTIONS)}")
    base, axis_order = CONVENTIONS[convention]
    if base == "pixels":
        width, height = meta.get("output_width"), meta.get("output_height")
        if width is None or height is None:
            width, height = meta["output_size"]
    else:
        width = height = float(base)
    ((x0, y0, x1, y1),) = normalize_coordinates([box], width, height, crop=meta.get("crop"), axis_order=axis_order)
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def preview_call(source: str, candidates: list[dict[str, Any]], convention: str, meta: dict[str, Any]) -> dict:
    """Build the arguments for preview_image_bboxes with index labels for the correction round."""
    objects = []
    for index, cand in enumerate(candidates):
        objects.append({"bbox": to_normalized(cand["box"], convention, meta), "label": f"{index}:{cand['label']}"})
    return {"source": source, "objects": objects, "grid": {}}
