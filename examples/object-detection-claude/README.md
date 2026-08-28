# object-detection-claude

Box every cat in the COCO 2017 val images that contain cats — classes `black_cat`, `white_cat`,
`other_cat` — with an execution agent built on the
[Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/python). The agent looks at the
[annotools](../../README.md) grid preview, proposes boxes in pixel coordinates of the shown image (Claude's documented preference), sees
them rendered with index labels, corrects by index (at most 3 rounds), and commits to SQLite.

## Run

```bash
UV_PROJECT_ENVIRONMENT=.venv uv sync   # own environment (annotools is a path dependency); just recipes set this too
export ANTHROPIC_API_KEY=...  # the SDK bundles the Claude Code binary; no separate install
just init-db
just download 20              # trial subset (all ~184 cat images: just download)
just trial 3                  # saves overlays to workspaces/coco-cats/data/interim/trial and prints boxes
just run                      # every pending item, 4 workers
just export                   # workspaces/coco-cats/output/detections.jsonl
just sanity                   # mean IoU against the COCO cat boxes (informational)
```

If your shell exports `UV_PROJECT_ENVIRONMENT` globally (the annotools devcontainer does), run
`UV_PROJECT_ENVIRONMENT=$PWD/.venv uv sync` here so this project keeps its own environment.

Spec: `spec/task.md`; system prompt: `spec/prompts/system.md`; configuration: `config/default.json`.
Agents working in this directory read `CONTEXT.md` first.

## How it works

One `query()` per image with three tools: `look_at_item` (768 px preview + the configured grid, returns the shown
size), `propose_boxes` (cleans the candidates — class list, ≥ 1 % area, IoU-duplicate removal — draws them
with index labels on the same gridded view, counts a round), `commit_boxes` (stores `bbox` rows with
label, confidence, and rounds, replacing the item's earlier commit in this run; `needs_review` unless the
model declared the overlay correct and every confidence is ≥ `confidence_floor`; an empty commit stores a
`no_object` tag with the same status rule). `config/default.json` sets `coordinates: "pixels"` and the 768 px preview from the
`mllm-multimodal-input` size table; Claude answers in pixel coordinates because its docs
say normalized requests work poorly; `geometry.py` maps them back through the preview metadata.

## Usage record

| Field | Value |
|---|---|
| Model | `claude-opus-5` (effort `medium`, 768 px JPEG preview, 10×10 grid, `coordinates: "pixels"`, max 3 rounds, `max_budget_usd_per_item` 0.30) |
| Items | 3 (`just trial 3`, 2026-08-28, run 1; 0 `needs_review`) |
| Mean rounds per image | 1.0 |
| Input / output tokens | 24 / 1,222 (cache read 60,379; cache creation 15,616) |
| Cost (USD, SDK estimate) | 0.220 (0.073 per image) |
| Wall time | 67.1 s summed over items (4 workers) |
| Sanity: mean best IoU / recall@0.5 | 0.913 / 1.0 on 3 COCO boxes (`just sanity`) |

Fill this table from the JSON summary `just run` prints (`cost_usd`, `seconds`, `items`, `mean_rounds`)
and `just sanity`; `total_cost_usd` is a client-side estimate, not a bill.
