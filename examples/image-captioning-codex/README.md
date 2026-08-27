# image-captioning-codex

Caption the COCO 2017 val images that contain cats with an execution agent built on the
[Codex SDK](https://github.com/openai/codex/tree/main/sdk/python) (`openai-codex`, which bundles the Codex runtime), using
[annotools](../../README.md) previews for cheap image input and SQLite as the store. Four variants per
image: `long`, `medium`, `short` (by successive compression), and `tags`.

## Run

```bash
UV_PROJECT_ENVIRONMENT=.venv uv sync   # own environment (annotools is a path dependency); just recipes set this too
# authenticate once: `uv run python -c "from openai_codex import Codex; Codex().login_api_key('sk-...')"` or reuse an existing Codex login
just init-db
just download 20              # trial subset (all ~184 cat images: just download)
just trial 3                  # prints image paths and the four variants for you to check
just run                      # captions every pending item with 4 workers
just export                   # workspaces/coco-cats/output/captions.jsonl
```

Spec: `spec/task.md`; prompts: `spec/prompts/`; configuration: `config/default.json`. Agents working
in this directory read `CONTEXT.md` first.

## How it works

One Codex thread per image (`cwd` = the workspace, read-only sandbox): the tools are a FastMCP stdio
server (`python -m captioning.tools`) registered through the thread config; the agent calls
`look_at_item` (annotools preview at 768 px), writes the long caption, compresses it twice, produces
tags, and records each with `record_caption` / `record_tags` (SQLite, schema from the
`sqlite-annotation-store` skill). The pipeline verifies that all four variants
exist and are within budget; on failure it sets the item's rows to `needs_review` (nothing is overwritten
and the item stays pending for the next run) and stops the run after 10 failures in a row.

## Usage record

| Field | Value |
|---|---|
| Model | _pending first full run_ |
| Items | _pending_ |
| Input / cached / output / reasoning tokens | _pending_ |
| Cost (USD, from the provider dashboard) | _pending_ |
| Wall time | _pending_ |

Fill this table from the JSON summary `just run` prints (`items`, `seconds`, `input_tokens`,
`cached_input_tokens`, `output_tokens`, `reasoning_output_tokens` from `TurnResult.usage.total`); the Codex
SDK does not estimate cost, so take the amount from the provider dashboard.
