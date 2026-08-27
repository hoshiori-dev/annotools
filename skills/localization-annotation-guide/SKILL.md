---
name: localization-annotation-guide
description: >-
  Guides an agent through localization annotation — bounding boxes, rotated boxes, keypoints,
  polygons, segmentation — with the annotools previews: which coordinate format to request and
  store, the grid-then-verify loop with a bounded number of correction rounds, rectangle checks for
  rotated boxes, and quality controls. Use when designing or running an object-detection,
  keypoint, polygon, or segmentation labelling pipeline, when a model's boxes look shifted, or when
  deciding how many self-correction rounds to allow. Not for captioning or text-only labels.
---

# Localization Annotation Guide

## Representation

- **Store** boxes as normalized `[x_min, y_min, x_max, y_max]` (0–1, relative to the uncropped
  source), polygons as flat `[x1, y1, …]`, rotated boxes as DOTA-style 8 numbers (4 corners,
  clockwise from top-left). This is the annotools convention and what the project's annotation store
  expects.
- **Ask** each model in the convention it is trained for (`mllm-multimodal-input` → "Coordinate
  conventions by model"): Claude and Qwen2.5-VL answer in pixels of the image they saw (`pixels`);
  GPT/Codex in a fixed 0..999 `[x_min, y_min, x_max, y_max]` space (`gpt`); Gemini in
  `[ymin, xmin, ymax, xmax]` × 1000 (`thousand_yx`); Qwen3-VL in 0–1000 xyxy (`thousand`). Convert in
  code with the `normalize_coordinates` tool or `assets/build_preview_call.py` (convention names in
  parentheses) using the preview metadata (`output_width`/`output_height`, `crop`).
- Rotated boxes: request `(cx, cy, w, h, theta)` **or** 4 corners, convert with
  `rotated_bbox_to_polygon`, and verify rectangularity with `is_rectangle`
  ([assets/check_rectangle.py](assets/check_rectangle.py)).

## The detection loop (default ≤ 3 correction rounds — confirm the number with the user)

1. **Look**: `preview_image_grid(source, columns=10, rows=10)` — 9 lines each way, 50 % white.
   Denser or sparser grids reduce accuracy in practice; keep 10×10 unless the objects are tiny, then
   `crop` a region and run the loop on the crop.
2. **Propose**: the model returns candidates in its native convention with labels and confidence.
   Convert to normalized xyxy; clamp to [0, 1]; drop boxes with zero area.
3. **Verify**: `preview_image_bboxes(source, objects=[...], grid={})` with the candidate list
   ([assets/build_preview_call.py](assets/build_preview_call.py)); each box carries an index label so
   the model can name what to move.
4. **Correct**: ask for adjustments *by index* ("move box 2's right edge to the object's edge") and
   re-render. Box labels from the asset are 0-based; polygon vertex numbers drawn by
   `preview_image_polygons` are 1-based — say which you mean in the prompt. Stop when the model says the overlay is acceptable or the round limit is reached.
5. **Commit**: write the final list with the round count and the model's self-assessment through the
   project's annotation-store write tool; never write intermediate rounds as final.
   Done when: every image has either a committed annotation or a `needs_review` flag with the last
   overlay saved (`save_to`).

## Variants

- **Keypoints**: same loop with `preview_image_keypoints`; ask for visibility per point; skeleton
  order fixed in the spec.
- **Polygons / instance masks**: `preview_image_polygons` (vertex indices on) to check order; for
  masks compare with `preview_image_segmentation` (label or legend mode).
- **Rotated boxes**: after conversion, reject candidates failing `is_rectangle` and ask again.
- **Video**: sample with `preview_video_grid`, annotate keyframes, interpolate in code, verify the
  interpolated frames with `preview_image_bboxes` on frames saved via `save_to`.

## Quality controls

- Class definitions with include/exclude rules and confusable pairs sit in the system prompt (cached).
- Reject: boxes outside the image, area < spec minimum, duplicate IoU > 0.9, labels outside the class
  list.
- Sample 5 % of committed items for a second pass with a different seed/model; log disagreement.
- Track rounds used per item; a rising average means the prompt or grid setting drifted.

## Gotchas

- A model that returns normalized coordinates when asked for pixels (or vice versa) shifts every box
  — assert the value range before converting.
- Claude resizes images above its tier limits and answers in the resized space; any annotools preview
  ≤ 1092 px on both sides stays under the standard tier, but a larger `max_width`/`max_height` or a raw
  upload would trigger it — then normalize by the resized size, not the original.
- Rendering candidates without the grid loses the anchor the model used; keep `grid={}` in the
  verification call.
- `preview_image_polygons` rejects coordinates outside 0–1 — clamp rotated-box corners first.
