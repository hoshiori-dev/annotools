# object-detection-claude

Box every cat in the COCO 2017 val images that contain cats — classes `black_cat`, `white_cat`,
`other_cat` — with an execution agent built on the
[Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/python). The agent looks at the
[annotools](../../README.md) grid preview, proposes boxes in pixel coordinates of the shown image, sees
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

One `query()` per image with three tools: `look_at_item` (768 px preview + 10×10 grid, returns the shown
size), `propose_boxes` (cleans the candidates — class list, ≥ 1 % area, IoU-duplicate removal — draws them
with index labels on the same gridded view, counts a round), `commit_boxes` (stores `bbox` rows with
label, confidence, and rounds, replacing the item's earlier commit in this run; `needs_review` unless the
model declared the overlay correct and every confidence is ≥ `confidence_floor`; an empty `done=true`
commit stores a `no_object` tag). Claude answers in pixel coordinates because its docs
say normalized requests work poorly; `geometry.py` maps them back through the preview metadata.

## Usage record

| Field | Value |
|---|---|
| Model | _pending first full run_ |
| Items | _pending_ |
| Mean rounds per image | _pending_ |
| Input / output tokens | _pending_ |
| Cost (USD, SDK estimate) | _pending_ |
| Wall time | _pending_ |
| Sanity: mean best IoU / recall@0.5 | _pending_ (`just sanity`) |

Fill this table from the JSON summary `just run` prints (`cost_usd`, `seconds`, `items`, `mean_rounds`)
and `just sanity`; `total_cost_usd` is a client-side estimate, not a bill.
