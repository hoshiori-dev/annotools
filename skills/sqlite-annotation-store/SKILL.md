---
name: sqlite-annotation-store
description: >-
  Sets up and operates the SQLite store for an annotation project — prebuilt schema for items, runs,
  and every annotation kind, file-pointer rules, the record/update tool contract for execution
  agents, and exports to jsonl, csv, parquet, or webdataset. Use when creating a dataset.db, when an
  agent needs tools to write or update labels, when exporting annotations, or when someone proposes
  storing images or masks inside the database. Not for choosing the task or for other engines.
compatibility: Scripts need Python 3.10+ with the standard library; parquet export needs pyarrow.
---

# SQLite Annotation Store

One database per workspace at `workspaces/<task>/data/dataset.db`. Rows store **pointers** to files
(local path or fsspec URL) and JSON annotations in the annotools conventions (normalized 0–1
coordinates relative to the uncropped source; boxes `[x_min, y_min, x_max, y_max]`; polygons
`[x1, y1, …]`; rotated boxes as 8 numbers). Bytes never enter the database.

## Workflow

1. **Create**: `python scripts/init_db.py --db workspaces/<task>/data/dataset.db --task detection`
   applies [assets/schema.sql](assets/schema.sql) and registers the task in `meta`
   ([scripts/init_db.py](scripts/init_db.py)). Idempotent — safe to re-run.
2. **Ingest items**: one row per source file in `items` (`uri`, `media_type`, `width`, `height`,
   `duration`, `meta_json`). Use `INSERT OR IGNORE` keyed by `uri`.
3. **Open a run**: a `runs` row per pipeline execution (model, prompt hash, config json, started_at).
   Every annotation carries `run_id`, so re-runs never overwrite each other.
4. **Give the execution agent three tools**: `record_annotation`, `update_annotation`,
   `mark_reviewed`; writes are idempotent on `(item_id, run_id, kind, key)`. Read
   [references/tool-contract.md](references/tool-contract.md) when implementing them (SDK wiring is
   in the `agent-vision-tools` skill of this catalog).
5. **Export**: `python scripts/export.py --db … --format jsonl --out output/` writes one line per item
   with its final annotations, each as `{kind, key, label, confidence, rounds, payload}`
   ([scripts/export.py](scripts/export.py)); `csv` flattens to one row per annotation, `parquet`
   keeps one row per item, `webdataset` writes a tar of `<sha1(uri)[:16]>.json` records (media stays where
   `uri` points; copy it in your own step if the consumer needs it inside the tar).
   Done when: every item is either exported or listed in the export's `skipped` summary with a reason.

## Schema (assets/schema.sql)

| Table | Purpose | Key columns |
|---|---|---|
| `meta` | task name, schema version, conventions | `key`, `value` |
| `items` | one row per source file | `id`, `uri` (unique), `media_type`, `width`, `height`, `duration`, `split`, `meta_json` |
| `runs` | one row per pipeline execution | `id`, `model`, `prompt_sha256`, `config_json`, `started_at`, `finished_at` |
| `annotations` | one row per label unit | `id`, `item_id`, `run_id`, `kind` (`bbox`, `polygon`, `keypoints`, `rbox`, `caption`, `tag`, `mask`, `segment`), `key`, `label`, `payload_json`, `confidence`, `rounds`, `status` (`draft`/`final`/`needs_review`/`rejected`), `created_at`, `updated_at` |
| `reviews` | second-pass verdicts | `annotation_id`, `reviewer`, `verdict`, `note`, `created_at` |

`payload_json` shapes: bbox `{"bbox": [x0, y0, x1, y1]}`; polygon `{"points": [...]}`; keypoints
`{"points": [[x, y, v], ...]}`; rbox `{"corners": [8 numbers]}`; caption `{"text": "...", "variant":
"long"}`; tag `{"tags": [...]}`; mask `{"uri": "...mask.png", "ids": {"1": "cat"}}` (a pointer);
segment `{"start": s, "end": s}` (the label lives in the `label` column). Views: `final_annotations`
(for each item **and kind**, the rows of the latest run with a final row of that kind — a caption from
run 1 survives a bbox-only run 2), `items_pending` (items with no final row), and `task_annotations`
(final rows of the kinds that belong to the task chosen at `init_db`).

## Rules

- File pointers only: masks, crops, and previews are files under `data/interim/`; the DB stores
  their URI.
- Never delete: mark `rejected`; exports select `status = 'final'` from the latest run per item.
- One source of truth for conventions: `meta` rows `coordinate_convention = normalized_xyxy`,
  `schema_version`; the export refuses to run on a different version.
- Concurrency: SQLite in WAL mode (`init_db.py` sets it); one writer per run, many readers.
- Every connection runs `PRAGMA foreign_keys = ON` (not persisted by SQLite); the scripts do.
- Design note: one `annotations` table keyed by `kind` replaces per-kind tables — one tool contract,
  one export path, and the `(item_id, run_id, kind, key)` uniqueness holds everywhere.

## Gotchas

- Storing JSON arrays as text is intentional; index `items.uri` and `annotations(item_id, run_id,
  kind)` — both are in the schema.
- `INSERT OR REPLACE` changes rowids and breaks `reviews` references; use `ON CONFLICT DO UPDATE`
  (the scripts do).
- Parquet needs `pyarrow`; the script errors with the install hint instead of silently writing csv.
- A run without `prompt_sha256` cannot be audited later — hash the full cached prefix.

## References

- Read [references/tool-contract.md](references/tool-contract.md) when building the execution
  agent's write tools.
- Read [references/swapping-engines.md](references/swapping-engines.md) only when the project
  refuses SQLite.
