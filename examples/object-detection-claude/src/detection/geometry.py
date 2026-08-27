"""Coordinate helpers for the detection pipeline (pixels of the shown preview ↔ normalized source)."""

from typing import Any


def pixels_to_normalized(box: list[float], meta: dict[str, Any]) -> list[float]:
    """Map a pixel box of the shown preview to normalized xyxy of the uncropped source, clamped to [0, 1]."""
    w, h = meta["output_size"]
    cx0, cy0, cx1, cy1 = meta["crop"]
    sx, sy = cx1 - cx0, cy1 - cy0
    x0, y0, x1, y1 = box
    out = [cx0 + x0 / w * sx, cy0 + y0 / h * sy, cx0 + x1 / w * sx, cy0 + y1 / h * sy]
    out = [min(max(float(v), 0.0), 1.0) for v in out]
    if out[0] > out[2]:
        out[0], out[2] = out[2], out[0]
    if out[1] > out[3]:
        out[1], out[3] = out[3], out[1]
    return out


def iou(a: list[float], b: list[float]) -> float:
    ix0, iy0, ix1, iy1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def clean(
    boxes: list[dict[str, Any]], meta: dict[str, Any], classes: set[str], max_boxes: int = 20
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
        bbox = pixels_to_normalized([float(v) for v in raw], meta)
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
