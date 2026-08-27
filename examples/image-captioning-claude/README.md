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
| Model | _pending first full run_ |
| Items | _pending_ |
| Input / output tokens | _pending_ |
| Cost (USD, SDK estimate) | _pending_ |
| Wall time | _pending_ |

Fill this table from the JSON summary `just run` prints (`items`, `input_tokens`, `output_tokens`,
`cache_read_input_tokens`, `cache_creation_input_tokens`, `cost_usd`, `seconds`); `cost_usd` sums the SDK's client-side estimates, not a bill.
