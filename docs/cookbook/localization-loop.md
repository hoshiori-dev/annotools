# Run the localization loop

Boxes, keypoints, polygons, and masks share one procedure: the model looks at a gridded preview,
proposes candidates, sees its own candidates drawn back onto the same view, corrects them by index,
and commits — within a number of rounds agreed in the [interview](interview.md), three by default.
Captioning has no such loop; localization does, because a model cannot judge a coordinate it has not
seen rendered.

1. **Look** — `preview_image_grid(source, columns=10, rows=10)`. The grid is the anchor: ten cells
   each way, so nine lines. Denser or sparser grids measure worse in practice. Tiny objects get a
   `crop` and the loop runs on the crop, not a larger preview.
2. **Propose** — candidates in the model's native convention, with labels and confidence. Convert to
   normalized xyxy immediately, clamp to [0, 1], drop zero-area boxes.
3. **Verify** — `preview_image_bboxes(source, objects=[...], grid={})` with the same grid, each box
   carrying an index label.
4. **Correct** — ask for adjustments by index ("move box 2's right edge to the ear"), re-render,
   repeat until the model calls the overlay acceptable or the round limit is reached. Every round
   counts, including one that changes nothing.
5. **Commit** — one write with the final list, the round count, and the model's self-assessment.
   Intermediate rounds are never written as final; an item that exhausts its rounds is committed as
   `needs_review` with the last overlay saved.

Three ways to lose accuracy in this loop, all silent: rendering the verification overlay without the
grid the model proposed on, re-ordering the boxes between rounds so the indices move under the
model, and mixing index bases — the box labels drawn by the skill's asset are 0-based while
`preview_image_polygons` numbers vertices from 1, so the prompt has to say which.

## Ask in the model's convention, store in yours

Storage is always normalized 0–1 relative to the uncropped source. Prompting is not: every model
localizes best in the frame it was trained on, and Claude's documentation says so explicitly.
Ask natively, then convert in code. Never ask a model to normalize.

--8<-- "skills/mllm-multimodal-input/SKILL.md:coordinates"

The conversion is one call, with `base` the frame the model answered in and `crop` taken from the
preview metadata:

```python
from annotools import normalize_coordinates

# Gemini answers [ymin, xmin, ymax, xmax] in a 0-1000 space; the preview showed the full frame.
boxes = normalize_coordinates([[113, 21, 897, 494]], 1000, 1000, axis_order="yx")
# [[0.021, 0.113, 0.494, 0.897]]
```

Gemini's y-first order is the most common silent bug in this step: swapped axes still produce
plausible boxes. Assert the value range of the answer before converting — pixel answers stay under
`output_width`, fixed-space answers reach toward 1000 even on a small image — and a model that
answers in the wrong convention will be obvious rather than merely wrong.

## Variants and quality gates

Keypoints use the same loop with `preview_image_keypoints` and a per-point visibility value;
polygons use `preview_image_polygons` with vertex indices on, or
`preview_image_segmentation` for masks; rotated boxes are converted with `rotated_bbox_to_polygon`
and rejected when `is_rectangle` fails; video keyframes are annotated, interpolated in code, and the
interpolated frames verified as images.

Before anything is rendered, reject boxes outside the image, below the spec's minimum area,
duplicated at IoU > 0.9, or carrying a label outside the class list, and report the rejection back
to the model. After the run, sample 5 % for a second pass with a different seed or model and log
disagreement. Track rounds per item: a rising average means the prompt or the grid setting drifted.

## What it measures

Both detection examples ran the loop on three COCO cat images at a 768 px preview with a 10×10 grid
and a three-round limit on 2026-08-28:

| | [`object-detection-claude`](https://github.com/hoshiori-dev/annotools/tree/main/examples/object-detection-claude) | [`object-detection-codex`](https://github.com/hoshiori-dev/annotools/tree/main/examples/object-detection-codex) |
|---|---|---|
| Coordinates asked for | pixels of the shown image | fixed 0..999 space |
| Mean rounds per image | 1.0 | 0.67 (1.0 over the two finished images) |
| Mean best IoU vs. the COCO boxes | 0.913 | 0.929 after run 1 (2 images); 0.866 after the retry (3 images) |
| Recall @ 0.5 IoU | 1.0 | 1.0 |
| `needs_review` | 0 of 3 | 1 of 3 (no box committed; a retry finished it in one round) |

One round is the common case: the first proposal, seen rendered, is usually accepted. The IoU
figures are informational — the COCO boxes are a reference, not the specification — and three
images is a sanity check, not a benchmark.

Next: [give the execution agent the tools](sdk-tools.md) this loop assumes.

Source: [`skills/localization-annotation-guide`](https://github.com/hoshiori-dev/annotools/tree/main/skills/localization-annotation-guide),
with the coordinate table from [`skills/mllm-multimodal-input`](https://github.com/hoshiori-dev/annotools/tree/main/skills/mllm-multimodal-input)
and the pipeline skeleton in [`skills/task-object-detection`](https://github.com/hoshiori-dev/annotools/tree/main/skills/task-object-detection)
