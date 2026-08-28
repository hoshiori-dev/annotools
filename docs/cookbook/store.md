# Choose a store

One SQLite file per workspace, at `workspaces/<task>/data/dataset.db`. It holds pointers and JSON,
never bytes: an image stays where it is, a mask is a PNG under `data/interim/` and the row records
its URI. A database that swallows media stops being copyable, diffable, or cheap to open, and the
media is already on disk.

Five tables carry every task family:

| Table | One row per | Notes |
|---|---|---|
| `meta` | setting | task name, `schema_version`, `coordinate_convention` |
| `items` | source file | `uri` is unique; local path or fsspec URL |
| `runs` | pipeline execution | model, `prompt_sha256`, config, timestamps |
| `annotations` | label unit | `kind` ∈ bbox, polygon, keypoints, rbox, caption, tag, mask, segment |
| `reviews` | second-pass verdict | accept / reject / fix |

One `annotations` table keyed by `kind` rather than a table per kind is what makes the rest cheap:
one write contract, one export path, and one uniqueness rule — `(item_id, run_id, kind, key)` — that
holds for a caption variant and a box index alike. `payload_json` carries the kind-specific shape
(`{"bbox": [x0, y0, x1, y1]}`, `{"text": …, "variant": …}`, `{"points": …}`), always in normalized
0–1 coordinates relative to the uncropped source.

## Runs, not overwrites

Every annotation carries a `run_id`, so a second pass never destroys the first. The
`final_annotations` view resolves this per item **and kind**: for each pair it takes the rows of the
latest run that produced a final row of that kind. A caption written in run 1 survives a
boxes-only run 2. `items_pending` is its complement — items with nothing final yet — and is what a
pipeline iterates, which makes re-running after a partial failure the same command as the first run.

Nothing is deleted. A bad annotation is marked `rejected`; a doubtful one `needs_review`, which
keeps it out of `final_annotations` and therefore keeps its item pending.

## What the execution agent gets

Three tools, no SQL: `record_annotation` (upsert on the uniqueness key, payload shape validated per
kind, `run_id` fixed by the pipeline and never chosen by the agent), `update_annotation` (current
run only; `final → draft` is refused), and `mark_reviewed` (writes a `reviews` row; `accept`
promotes a `needs_review` row back to `final`). The SDK wiring for them is
[step 5](sdk-tools.md); the full contract is in the skill's
[`references/tool-contract.md`](https://github.com/hoshiori-dev/annotools/blob/main/skills/sqlite-annotation-store/references/tool-contract.md).

Two operational details bite everyone once: `PRAGMA foreign_keys = ON` is connection-scoped, so
every connection has to set it, and `INSERT OR REPLACE` changes rowids, which silently breaks the
`reviews` references — use `ON CONFLICT DO UPDATE`. The shipped scripts do both.

## The schema

`python scripts/init_db.py --db workspaces/<task>/data/dataset.db --task detection` applies it, sets
WAL mode, records the conventions in `meta`, and adds a `task_annotations` view for the kinds that
belong to the chosen task. It is idempotent.

??? example "skills/sqlite-annotation-store/assets/schema.sql"

    ```sql
    --8<-- "skills/sqlite-annotation-store/assets/schema.sql"
    ```

The schema is plain SQL with JSON text columns, so PostgreSQL or DuckDB run it with small edits if a
project refuses SQLite; keep the tables, the uniqueness key, and the `final_annotations` semantics
and the tool contract and export still apply.

Next: [fit the model's token budget](token-budget.md) before the first item is sent anywhere.

Source: [`skills/sqlite-annotation-store`](https://github.com/hoshiori-dev/annotools/tree/main/skills/sqlite-annotation-store)
