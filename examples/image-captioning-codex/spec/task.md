# COCO cats — image captioning (Codex SDK)

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
- Model: Codex/GPT (configured in `config/default.json`, default `gpt-5.6-terra`); effort `low`.
- Preview: `max_width`/`max_height` 768 (patch-model cost ≈ 700 tokens per image); no grid.
- Prompt layout: static rules (cached system prompt) → item id → image → question. Accepted trial
  outputs may be appended to the system prompt as examples once the trial passes.

## Procedure
Linear, parallel (`workers` in config): preview → long → compress ×2 → tags → four writes.

## Quality control
- Accept when all four variants are present and `medium`/`short` are within their word budgets;
  otherwise every row of the item in this run is set to `needs_review` and an error row
  (`caption`/`error`) records the reason — nothing already written is overwritten and the item stays
  in `items_pending` for the next run.
- Second pass: 5 % sample reviewed by a human via `just review` (prints image path + captions).

## Output contract
- Store: `data/dataset.db` (schema from `sqlite-annotation-store`, task `captioning`).
- Export: `workspaces/coco-cats/output/captions.jsonl` — one line per image:
  `{"uri", "coco_id", "long", "medium", "short", "tags"}` (`scripts/export_captions.py`).

## Budget
- No per-item cost guard (the Codex SDK reports tokens, not cost); ≤ 4 workers; stop the run after
  10 failures in a row (`max_failures`); token totals are reported in the run summary.
