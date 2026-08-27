# image-captioning-claude

Example project: caption the COCO 2017 val images that contain cats with an execution agent built on
the Claude Agent SDK, using annotools previews for cheap image input and SQLite as the store. This
directory is independent of the repository root: read this file first, not the root AGENTS.md.

## Map
- `spec/task.md` — the contract (read first); `spec/prompts/` — prompt templates (static, cached)
- `config/default.json` — model, effort, preview size, workers, budgets
- `src/captioning/` — pipeline (`pipeline.py`), execution-agent tools (`tools.py`), store access (`store.py`)
- `scripts/` — `download_coco_cats.py`, `init_db.py` (copied from the store skill), `export_captions.py`
- `skills/` — the annotools skills this project follows (copies, pinned)
- `template/workspace/` — empty workspace layout to copy for a new dataset
- `workspaces/coco-cats/` — `data/raw` (read-only), `data/interim`, `data/dataset.db`, `output/`

## Rules
- Never modify `data/raw/`; the DB stores file pointers only.
- The execution agent sees only `workspaces/coco-cats/` (tool confinement in `src/captioning/tools.py`).
- Changing `spec/` needs the user's confirmation; prompts and export follow the spec.
- Development checks: `just check` (ruff, ty, pytest) — the repository CI does not run this project.
- The justfile exports `UV_PROJECT_ENVIRONMENT=.venv`; when running `uv` directly, set it too.

## Commands
`just init-db` · `just download [limit]` · `just trial [n]` · `just run` · `just export` · `just check`

## Usage record
See README.md (filled after a full run).
