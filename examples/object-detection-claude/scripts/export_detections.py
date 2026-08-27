#!/usr/bin/env python3
"""Export final boxes to output/detections.jsonl.

Record shape: {"uri", "coco_id", "boxes": [{"bbox", "label", "confidence", "rounds"}]}.

Usage: python scripts/export_detections.py --db <dataset.db> --out <detections.jsonl>
Images whose final rows are only the `no_object` tag export with an empty box list. Exit codes: 0 ok, 2 bad arguments.
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
        "SELECT i.uri, i.meta_json, a.kind, a.key, a.label, a.confidence, a.rounds, a.payload_json "
        "FROM final_annotations a JOIN items i ON i.id = a.item_id ORDER BY i.id, CAST(a.key AS INTEGER)"
    ).fetchall()
    per_item: dict[str, dict] = {}
    for uri, meta_json, kind, _key, label, confidence, rounds, payload in rows:
        rec = per_item.setdefault(
            uri, {"uri": uri, "coco_id": json.loads(meta_json or "{}").get("coco_id"), "boxes": []}
        )
        if kind == "bbox":
            rec["boxes"].append(
                {"bbox": json.loads(payload)["bbox"], "label": label, "confidence": confidence, "rounds": rounds}
            )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for rec in per_item.values():
            fh.write(json.dumps(rec) + "\n")
    print(
        json.dumps({"path": str(out), "items": len(per_item), "boxes": sum(len(r["boxes"]) for r in per_item.values())})
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
