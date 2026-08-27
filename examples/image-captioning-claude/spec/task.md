# COCO cats — image captioning (Claude Agent SDK)

## Goal
Produce four caption variants per image for the COCO 2017 val images that contain at least one cat:
`long`, `medium`, `short`, and `tags`. The consumer is a caption-training/eval set; captions describe
only what is visible.

## Inputs
- Source: `workspaces/coco-cats/data/raw/coco-cats/` — COCO val2017 images with category `cat`
  (≈ 184 images), downloaded by `scripts/download_coco_cats.py`; read-only.
- Items registered in `data/dataset.db` (`items.uri` relative to the workspace, `meta_json.coco_id`).

## Labels
- `long` ≤ 60 words: subject → action → setting → notable details → visible text (quoted).
- `medium` ≤ 25 words and `short` ≤ 10 words: compressed from `long`, keep subject + action + setting.
- `tags`: 3–8 lowercase singular nouns/adjectives, free vocabulary, JSON array.
- English, neutral register, present tense. No identities, brands, or speculation.

## Model and input
- Model: Claude (configured in `config/default.json`, default `claude-opus-5`); effort `low`.
- Preview: `max_width`/`max_height` 768 (Claude cost ≈ 450–800 tokens per image); no grid.
- Prompt layout: static rules + 2 accepted trial examples (cached) → item id → image → question.

## Procedure
Linear, parallel (`workers` in config): preview → long → compress ×2 → tags → four writes.

## Quality control
- Accept when all four variants are present and within budget; `needs_review` on any model or parse
  error (the error is stored in `payload.error`).
- Second pass: 5 % sample reviewed by a human via `just review` (prints image path + captions).

## Output contract
- Store: `data/dataset.db` (schema from `sqlite-annotation-store`, task `captioning`).
- Export: `workspaces/coco-cats/output/captions.jsonl` — one line per image:
  `{"uri", "coco_id", "long", "medium", "short", "tags"}` (`scripts/export_captions.py`).

## Budget
- ≤ 2 500 input + 400 output tokens per image; ≤ 4 workers; stop after 10 consecutive failures.
