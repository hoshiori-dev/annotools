"""Coordinate helpers for the detection pipeline (the model's frame ↔ normalized source)."""

from typing import Any, Literal

from annotools.geometry import normalize_coordinates

# config "coordinates" -> (base: "pixels" = the shown preview, or a fixed space; pair order on the model side)
CONVENTIONS: dict[str, tuple[str | float, Literal["xy", "yx"]]] = {
    "pixels": ("pixels", "xy"),  # Claude, Qwen2.5-VL: pixels of the image as shown
    "gpt": (999, "xy"),  # GPT / Codex: fixed 0..999 space (OpenAI GPT-5.4 vision tips)
    "thousand": (1000, "xy"),  # Qwen3-VL and other x-first 0-1000 spaces
    "thousand_yx": (1000, "yx"),  # Gemini: [ymin, xmin, ymax, xmax] * 1000
}


def box_to_normalized(box: list[float], meta: dict[str, Any], convention: str = "pixels") -> list[float]:
    """Map a box from the model's frame to normalized xyxy of the uncropped source, clamped to [0, 1].

    ``meta`` is the preview metadata of the view the model saw (``output_width``/``output_height``,
    ``crop``); ``convention`` selects the frame (see ``CONVENTIONS``). Swapped corners are reordered.
    """
    if convention not in CONVENTIONS:
        raise ValueError(f"unknown coordinates convention {convention!r}; expected one of {sorted(CONVENTIONS)}")
    base, axis_order = CONVENTIONS[convention]
    if base == "pixels":
        w, h = meta.get("output_width"), meta.get("output_height")
        if w is None or h is None:
            w, h = meta["output_size"]
    else:
        w = h = float(base)
    ((x0, y0, x1, y1),) = normalize_coordinates([box], w, h, crop=meta.get("crop"), axis_order=axis_order)
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def iou(a: list[float], b: list[float]) -> float:
    ix0, iy0, ix1, iy1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def clean(
    boxes: list[dict[str, Any]],
    meta: dict[str, Any],
    classes: set[str],
    max_boxes: int = 20,
    convention: str = "pixels",
) -> tuple[list[dict[str, Any]], list[str]]:
    """Normalize, validate, and de-duplicate candidate boxes; returns (kept, rejection reasons).

    Duplicates (IoU > 0.9 with an earlier kept box) are rejected and the earlier box is kept unchanged, so the
    indices the model reasons about stay stable; the message names the box it duplicates.
    """
    kept: list[dict[str, Any]] = []
    rejected: list[str] = []
    for index, b in enumerate(boxes):
        if len(kept) >= max_boxes:
            rejected.append(f"{index}: over the {max_boxes}-box limit")
            continue
        label = b.get("label")
        if label not in classes:
            rejected.append(f"{index}: unknown label {label!r}")
            continue
        raw = b.get("box")
        if not (isinstance(raw, list) and len(raw) == 4):
            rejected.append(f"{index}: box must be [x1, y1, x2, y2]")
            continue
        bbox = box_to_normalized([float(v) for v in raw], meta, convention)
        if (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) < 0.01:
            rejected.append(f"{index}: below 1 % of the image")
            continue
        confidence = float(b.get("confidence", 0.0))
        dup = next((i for i, k in enumerate(kept) if iou(k["bbox"], bbox) > 0.9), None)
        if dup is not None:
            rejected.append(f"{index}: duplicate of kept box {dup} (IoU > 0.9); merge them yourself if needed")
            continue
        kept.append({"bbox": bbox, "label": label, "confidence": confidence})
    return kept, rejected
