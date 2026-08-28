# image-captioning-claude

Caption the COCO 2017 val images that contain cats with an execution agent built on the
[Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/python), using
[annotools](../../README.md) previews for cheap image input and SQLite as the store. Four variants per
image: `long`, `medium`, `short` (by successive compression), and `tags`.

## Run

```bash
UV_PROJECT_ENVIRONMENT=.venv uv sync   # own environment (annotools is a path dependency); just recipes set this too
export ANTHROPIC_API_KEY=...  # the SDK bundles the Claude Code binary; no separate install
just init-db
just download 20              # trial subset (all ~184 cat images: just download)
just trial 3                  # prints image paths and the four variants for you to check
just run                      # captions every pending item with 4 workers
just export                   # workspaces/coco-cats/output/captions.jsonl
```

Spec: `spec/task.md`; prompts: `spec/prompts/`; configuration: `config/default.json`. Agents working
in this directory read `CONTEXT.md` first.

## How it works

One `query()` per image: the agent calls `look_at_item` (annotools preview at 768 px, the `mllm-multimodal-input` size for Claude), writes the long
caption, compresses it twice, produces tags, and records each with `record_caption` / `record_tags`
(SQLite, schema from the `sqlite-annotation-store` skill). The pipeline verifies that all four variants
exist and are within budget; on failure it sets the item's rows to `needs_review` (nothing is overwritten
and the item stays pending for the next run) and stops the run after 10 failures in a row.

## Usage record

| Field | Value |
|---|---|
| Model | `claude-opus-5` (effort `low`, 768 px JPEG preview, budgets medium 25 / short 10 words, `max_budget_usd_per_item` 0.25) |
| Items | 3 (`just trial 3`, 2026-08-28, run 1; 1 `needs_review` — short caption 11 > 10 words). One retry (`just run`, run 2, 1 item) hit the $0.25 item budget with the same 11-word short caption and stayed `needs_review`; `just export` wrote 2 items. |
| Input / output tokens | run 1: 24 / 2,108 (cache read 46,938; cache creation 15,482) — run 2: 4 / 285 (cache read 3,419; cache creation 5,297) |
| Cost (USD, SDK estimate) | run 1: 0.234 (0.078 per image) — run 2: 0.258 |
| Wall time | run 1: 69.0 s summed over items (4 workers) — run 2: 20.2 s |

Fill this table from the JSON summary `just run` prints (`items`, `input_tokens`, `output_tokens`,
`cache_read_input_tokens`, `cache_creation_input_tokens`, `cost_usd`, `seconds`); `cost_usd` sums the SDK's client-side estimates, not a bill.
