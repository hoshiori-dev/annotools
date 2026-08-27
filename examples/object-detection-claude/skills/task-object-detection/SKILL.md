---
name: task-object-detection
description: >-
  Scaffolds an object-detection project — class definitions with include/exclude rules and
  confusable pairs, prompt templates for the model's native coordinate convention, the
  trial-label-and-confirm step, the grid → propose → verify → correct (≤ N rounds) → commit pipeline
  skeleton with the annotools previews, and export. Use when asked to detect, box, or localize
  objects in images, when an interview settled on the detection family, or when a detection
  pipeline needs its prompts, loop, or quality checks. Not for captioning and not for the interview.
---

# Task scaffold: object detection

Detection is a loop: the agent looks at the gridded preview, proposes boxes in its model's native
convention, sees its own boxes rendered, corrects by index, and commits within a bounded number of
rounds (default 3 — confirm with the user in the interview).

## Workflow

1. **Class spec** from the `annotation-project-interview` detection branch: one-line definitions,
   include/exclude rules, confusable pairs, box extent rules (visible part, occlusion, minimum
   size), crowd handling. Write them into `spec/task.md`; they become the cached system prefix.
2. **Prompts** from [assets/prompts/propose.md](assets/prompts/propose.md) and
   [assets/prompts/correct.md](assets/prompts/correct.md). Pick the coordinate wording for the model
   (`mllm-multimodal-input` → "Coordinate conventions by model"): pixels of the shown image for
   Claude/Qwen2.5-VL, a fixed 0..999 xyxy space for GPT/Codex, `[ymin, xmin, ymax, xmax]`×1000 for
   Gemini, 0–1000 xyxy for Qwen3-VL; record the choice as `coordinates` in `config/`. Never ask a
   model to normalize — `normalize_coordinates` (or `build_preview_call.to_normalized`) does it.
3. **Trial**: 1–3 images through the full loop; write the final overlay bytes to
   `data/interim/trial/<item>.jpg` and show the user its path with the box list; adjust class rules;
   repeat until accepted.
4. **Pipeline** from [assets/pipeline_skeleton.py](assets/pipeline_skeleton.py): per item —
   `look_at_item(grid)` → propose → convert to normalized xyxy → `look_at_annotations` → correct by
   index (≤ N rounds) → `record_annotation` per box (`kind=bbox`, `key=<index>`, `label`,
   `confidence`, `rounds`); `needs_review` when the loop hit the limit with the model still unhappy
   **or** any box is below the confidence floor (a missing confidence counts as 0), else `final`. A
   negative image writes one `tag` row (`key=detection`, `["no_object"]`) so it leaves `items_pending`.
5. **Quality**: reject out-of-range or zero-area boxes and unknown labels before rendering; duplicate
   IoU > 0.9 → keep the higher confidence; sample 5 % for a second pass; track rounds per item.
6. **Export**: `export.py --format jsonl` → one line per image, boxes under `annotations`; convert to
   COCO in a post-step if required (spec decides).
   Done when: the trial passed, a full run finished with the agreed `needs_review` rate, and the
   README usage record is filled.

## Gotchas

- Render the verification overlay with the same grid the model proposed on; a different grid or
  crop invalidates the model's mental anchors.
- Index labels on the overlay are what the model refers to when correcting — keep them stable across
  rounds (re-render with the same order).
- Tiny objects: crop first (`crop` on the preview), run the loop on the crop, and map boxes back
  through the metadata — do not raise the preview size for the whole image.
- A round that changes nothing should end the loop early; count it as a round.
