"""Export final captions to output/captions.jsonl: {"uri", "coco_id", "long", "medium", "short", "tags"} per image.

Usage:
    python scripts/export_captions.py --db workspaces/coco-cats/data/dataset.db \
        --out workspaces/coco-cats/output/captions.jsonl
Items missing a variant are listed under "skipped" in the JSON summary. Exit codes: 0 ok, 1 error, 2 bad arguments.
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--db", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    if not Path(args.db).is_file():
        print(f"export: error: {args.db} not found", file=sys.stderr)
        return 2
    conn = sqlite3.connect(args.db)
    rows = conn.execute(
        "SELECT i.uri, i.meta_json, a.kind, a.key, a.payload_json FROM final_annotations a "
        "JOIN items i ON i.id = a.item_id ORDER BY i.id"
    ).fetchall()
    per_item: dict[str, dict] = {}
    for uri, meta_json, kind, key, payload in rows:
        rec = per_item.setdefault(uri, {"uri": uri, "coco_id": json.loads(meta_json or "{}").get("coco_id")})
        data = json.loads(payload)
        if kind == "caption":
            rec[key] = data.get("text")
        elif kind == "tag":
            rec["tags"] = data.get("tags")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    written, skipped = 0, []
    with out.open("w", encoding="utf-8") as fh:
        for uri, rec in per_item.items():
            missing = [k for k in ("long", "medium", "short", "tags") if not rec.get(k)]
            if missing:
                skipped.append({"uri": uri, "missing": missing})
                continue
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1
    print(json.dumps({"path": str(out), "items": written, "skipped": skipped}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
