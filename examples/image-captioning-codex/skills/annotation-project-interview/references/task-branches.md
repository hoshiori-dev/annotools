# Task branches — round-2 questions per task family

Ask only the branch that applies, with one recommendation per question.

## Captioning
1. Length budget per caption (words or tokens) and how many variants (long/medium/short/tags) [long → medium → short by successive compression; tags separately].
2. Focus order (subject, action, setting, style, text in image) [subject first].
3. Forbidden content (guessing identities, speculation, brand names) [no identities, no speculation].
4. Language and register [English, neutral, present tense].
5. Reasoning effort [lowest tier; captions are linear work].
6. Parallelism and batching [batch endpoint if latency is irrelevant].

## Detection (boxes)
1. Class list with one-line definitions; include/exclude rules per class; confusable pairs [propose from a 20-item sample].
2. What to box: whole object vs. visible part; occlusion and truncation rules; minimum size [visible extent; min 1 % of image area].
3. Crowd handling: label a group or every instance; cap per image [every instance up to 50].
4. Coordinate request convention per model and storage as normalized xyxy [from `mllm-multimodal-input`].
5. Correction-round limit and grid setting [3 rounds; 10×10 grid].
6. Confidence field and threshold for `needs_review` [yes; < 0.5].

## Keypoints
1. Skeleton definition and point order; visibility values [COCO-style 0/1/2].
2. Handling of partially visible subjects and multiple subjects.
3. Correction rounds [3].

## Polygons / instance segmentation
1. Polygon vs. raster mask output; vertex count limits [polygon, ≤ 50 vertices].
2. Holes and multi-part objects.
3. Verification mode: `preview_image_polygons` (vertex order) or `preview_image_segmentation` (mask).

## Rotated boxes
1. Angle convention (clockwise degrees, DOTA 8-number output) and the `is_rectangle` tolerance.
2. Whether to request `(cx, cy, w, h, theta)` or 4 corners [corners; convert and verify].

## Video events
1. Sampling rate and max frames per clip [1 fps, 32 frames]; segment boundaries at frame precision or seconds.
2. Event vocabulary and overlap rules.

## Audio segments
1. Segment types and minimum duration; sample rate for review clips [keep source rate].
2. Transcription needed? Which model?

## Shared (every family)
- Few-shot examples the user can provide (used in the cached prefix).
- Tie-breaking and "unknown" label policy.
- Export format details (field names, nesting, one line per item vs. per annotation).
- Budget guardrails: stop after N failures; cost cap per run.
