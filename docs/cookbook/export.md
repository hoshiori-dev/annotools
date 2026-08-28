# Export

The export is a read of the `final_annotations` view, so what it contains was decided long before it
runs: an item appears when it has a final row, and is listed under `skipped` with a reason when it
does not. Items in `needs_review` are held back rather than shipped with a caveat.

```bash
python scripts/export.py --db workspaces/<task>/data/dataset.db --format jsonl --out output/
```

| Format | Shape | Use it when |
|---|---|---|
| `jsonl` | one line per item, annotations nested | the default; anything downstream reads it |
| `csv` | one row per annotation, item columns repeated | spreadsheets, quick counts |
| `parquet` | one row per item (needs `pyarrow`) | large datasets, columnar reads |
| `webdataset` | tar of one `<key>.json` per item, `<key>` the first 16 hex characters of sha1(`uri`) | training loaders; media stays where `uri` points |

The record is the same in every format — this is one line of real `jsonl` output, from a store with
two committed boxes on one image:

```json
{"uri": "data/raw/coco-cats/000000039769.jpg", "media_type": "image", "width": 640, "height": 480, "duration": null, "split": "val", "meta": {}, "annotations": [{"kind": "bbox", "key": "0", "label": "other_cat", "confidence": 0.92, "rounds": 1, "payload": {"bbox": [0.021, 0.113, 0.494, 0.897]}}, {"kind": "bbox", "key": "1", "label": "other_cat", "confidence": 0.88, "rounds": 1, "payload": {"bbox": [0.482, 0.078, 0.985, 0.831]}}]}
```

Every annotation carries `kind`, `key`, `label`, `confidence`, `rounds`, and a kind-specific
`payload`, whatever the task family — a caption variant and a box index differ only in `kind` and
`key`. Coordinates are normalized 0–1 relative to the uncropped source, the convention the database
records in `meta.coordinate_convention`; a consumer that wants pixels multiplies by `width` and
`height`, and a consumer that wants COCO gets a post-step, because a conversion baked into the
export is a conversion nobody can audit.

The export refuses to run on a schema version it does not know. `rounds` travels with the data on
purpose: an annotation that took three correction rounds is a different thing from one accepted
immediately, and only the export carries that to whoever consumes the dataset.

## Media stays where it is

Nothing here copies files. `webdataset` writes JSON records whose `uri` points at the original
media; if the consumer needs the bytes inside the tar, that is a step you add, deliberately, with
knowledge of how large it will be. This is the same rule as [the store](store.md): pointers, never
bytes.

## What the examples exported

The four projects' trial runs on 2026-08-28 show the held-back path working, which is the part worth
seeing:

| Project | Items | Exported |
|---|---|---|
| [`object-detection-claude`](https://github.com/hoshiori-dev/annotools/tree/main/examples/object-detection-claude) | 3, none flagged | 3 |
| [`object-detection-codex`](https://github.com/hoshiori-dev/annotools/tree/main/examples/object-detection-codex) | 3, one `needs_review` | 3, after a retry committed the missing item as `final` |
| [`image-captioning-codex`](https://github.com/hoshiori-dev/annotools/tree/main/examples/image-captioning-codex) | 3, one `needs_review` | 3, after a retry recorded all four variants |
| [`image-captioning-claude`](https://github.com/hoshiori-dev/annotools/tree/main/examples/image-captioning-claude) | 3, one `needs_review` (an 11-word caption against a 10-word budget) | 2 — the retry reproduced the same caption, so the item stayed out |

Two of the three flagged items were exported after a second run, without touching the items that had
already passed, because the run id keeps the passes apart. The third stayed out, which is the
correct outcome for an item that does not meet the spec: it is visible in `items_pending`, and the
fix is the prompt, not the export.

That is the whole arc — [interview](interview.md), [store](store.md),
[token budget](token-budget.md), [localization loop](localization-loop.md),
[SDK tools](sdk-tools.md), [trial](trial-and-confirm.md), export.

Source: [`skills/sqlite-annotation-store`](https://github.com/hoshiori-dev/annotools/tree/main/skills/sqlite-annotation-store)
(`scripts/export.py`)
