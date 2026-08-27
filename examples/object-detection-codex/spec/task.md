# COCO cats — object detection (Codex SDK)

## Goal
Box every cat in the COCO 2017 val images that contain cats, labelled `black_cat`, `white_cat`, or
`other_cat`. The consumer is a detection eval set; boxes are normalized xyxy on the original image.

## Inputs
- Source: `workspaces/coco-cats/data/raw/coco-cats/` (≈ 184 images), downloaded by
  `scripts/download_coco_cats.py`; read-only. `meta_json.cat_boxes` keeps the COCO cat boxes for the
  informational IoU sanity check only — the agent never sees them.

## Labels
| Class | Definition | Exclude / confusable |
|---|---|---|
| `black_cat` | coat predominantly (≥ 80 %) black; small white patches allowed | dark tabby with visible stripes → `other_cat` |
| `white_cat` | coat predominantly (≥ 80 %) white; light cream counts as white | white with large colour patches → `other_cat` |
| `other_cat` | every other cat: tabby, ginger, calico, grey, mixed, or colour not determinable | — |
Box the visible extent of each cat (fur only, no shadows or reflections); truncated or occluded cats
are boxed by their visible part; cats smaller than 1 % of the image area are skipped; at most 20 boxes.
Toys, drawings, and statues of cats are not boxed.

## Model and input
- Model: Codex/GPT (`config/default.json`, default `gpt-5.6-terra`); effort `medium`.
- Preview: 768 px (`config/default.json` `preview`; GPT patch models bill 32-px patches by area, 768 ≈ 700
  tokens — the `mllm-multimodal-input` size table), 10×10 grid on every view.
- Coordinates (`config/default.json` `coordinates: "gpt"`): the model answers in a **fixed 0..999 space**
  `[x_min, y_min, x_max, y_max]`, the contract the OpenAI GPT-5.4 vision tips recommend; the pipeline
  normalizes with `annotools.geometry.normalize_coordinates` with base 999 × 999. Set `coordinates` to `pixels` and
  adjust `spec/prompts/system.md` to try pixel coordinates instead.
- Prompt layout: static class rules (cached) → item id → gridded image → question.

## Procedure
Grid preview (`look_at_item`) → propose (`propose_boxes`, indexed overlay) → correct by index (≤ 3
rounds) → `commit_boxes`; per box `kind=bbox`, `key=<index>`, `label`, `confidence`, `rounds`. A commit
replaces whatever the item had in this run.

## Quality control
- Before rendering: boxes are clamped to the image; unknown labels, boxes below 1 % of the image area,
  duplicates (IoU > 0.9 with an earlier kept box — the earlier one is kept, the later rejected by index),
  and boxes beyond `max_boxes` (20) are rejected and reported back to the model.
- `final` only when the model declares the overlay correct (`done=true`) and every confidence ≥
  `confidence_floor` (0.5); otherwise `needs_review` — including an empty commit with `done=false`. An
  empty commit writes a `tag`/`no_object` row with the same status rule (`final` only with `done=true`).
- `just sanity` reports mean IoU against the COCO cat boxes (informational, not a gate).

## Output contract
- Store: `data/dataset.db` (task `detection`).
- Export: `workspaces/coco-cats/output/detections.jsonl` — one line per image:
  `{"uri", "coco_id", "boxes": [{"bbox": [x0, y0, x1, y1], "label", "confidence", "rounds"}]}`.

## Budget
- ≤ 4 model calls per image (1 propose + ≤ 3 corrections); ≤ 4 workers; stop after 10 failures in a row
  (`max_failures`); `max_seconds_per_item` 300 bounds the wait for a runaway
  thread (the Codex SDK reports tokens, not cost).
