# object-detection-codex

Example project: box every cat (black / white / other) in the COCO 2017 val images that contain cats with
an execution agent built on the Codex SDK (`openai-codex`), using the annotools grid preview, an indexed overlay of
the agent's own boxes for self-correction (≤ 3 rounds), and SQLite as the store. This
directory is independent of the repository root: read this file first, not the root AGENTS.md.

## Map
- `spec/task.md` — the contract (read first); `spec/prompts/system.md` — the cached system prompt
- `config/default.json` — model, effort, preview/grid, classes, max rounds, confidence floor, workers, budgets
- `src/detection/` — pipeline (`pipeline.py`), the tools served to the agent as a FastMCP stdio server (`tools.py`: look_at_item / propose_boxes / commit_boxes), geometry (`geometry.py`), store access (`store.py`)
- `scripts/` — `download_coco_cats.py` (also keeps the COCO cat boxes in `meta_json` for the sanity check), `init_db.py` (from the store skill), `export_detections.py`, `sanity_iou.py`
- `skills/` — the annotools skills this project follows (copies, pinned)
- `template/workspace/` — empty workspace layout to copy for a new dataset
- `workspaces/coco-cats/` — `data/raw` (read-only), `data/interim`, `data/dataset.db`, `output/`

## Rules
- Never modify `data/raw/`; the DB stores file pointers only.
- The execution agent sees only `workspaces/coco-cats/` (Codex thread `cwd` + read-only sandbox; tool confinement in `src/detection/tools.py`); it never sees the COCO boxes.
- Changing `spec/` needs the user's confirmation; prompts and export follow the spec.
- Development checks: `just check` (ruff, ty, pytest) — the repository CI does not run this project.
- The justfile exports `UV_PROJECT_ENVIRONMENT=.venv`; when running `uv` directly, set it too.

## Commands
`just init-db` · `just download [limit]` · `just trial [n]` · `just run` · `just export` · `just sanity` · `just check`

## Usage record
See README.md (filled after a full run).
