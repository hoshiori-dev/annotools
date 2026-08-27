"""Turn model candidates into a preview_image_bboxes call and back.

Candidates arrive in the model's convention; this converts them to annotools' normalized xyxy using
the preview metadata returned by preview_image_grid, and builds the objects list with index labels.
"""

from typing import Any


def to_normalized(box: list[float], convention: str, meta: dict[str, Any]) -> list[float]:
    """Convert one candidate box to normalized xyxy relative to the uncropped source.

    conventions: "pixels" (Claude/Qwen/GPT: pixels of the preview), "gemini" ([ymin, xmin, ymax, xmax] * 1000).
    """
    if convention == "gemini":
        y0, x0, y1, x1 = (v / 1000 for v in box)
    elif convention == "pixels":
        w, h = meta["output_size"]
        x0, y0, x1, y1 = box[0] / w, box[1] / h, box[2] / w, box[3] / h
    else:
        raise ValueError(f"unknown convention {convention!r}")
    cx0, cy0, cx1, cy1 = meta["crop"]  # map from the cropped view back to the source frame
    sx, sy = cx1 - cx0, cy1 - cy0
    out = [cx0 + x0 * sx, cy0 + y0 * sy, cx0 + x1 * sx, cy0 + y1 * sy]
    return [min(max(v, 0.0), 1.0) for v in out]


def preview_call(source: str, candidates: list[dict[str, Any]], convention: str, meta: dict[str, Any]) -> dict:
    """Build the arguments for preview_image_bboxes with index labels for the correction round."""
    objects = []
    for index, cand in enumerate(candidates):
        objects.append({"bbox": to_normalized(cand["box"], convention, meta), "label": f"{index}:{cand['label']}"})
    return {"source": source, "objects": objects, "grid": {}}
