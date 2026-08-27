#!/usr/bin/env python3
"""Informational sanity check: mean best-match IoU between final boxes and the COCO cat boxes kept in items.meta_json.

Usage: python scripts/sanity_iou.py --db <dataset.db>
Prints JSON: images compared, mean IoU of each COCO box's best predicted match, recall at IoU >= 0.5.
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from detection.geometry import iou


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--db", required=True)
    args = parser.parse_args(argv)
    conn = sqlite3.connect(args.db)
    items = conn.execute("SELECT id, meta_json FROM items").fetchall()
    preds: dict[int, list[list[float]]] = {}
    for item_id, payload in conn.execute("SELECT item_id, payload_json FROM final_annotations WHERE kind = 'bbox'"):
        preds.setdefault(int(item_id), []).append(json.loads(payload)["bbox"])
    scores: list[float] = []
    compared = 0
    for item_id, meta_json in items:
        truth = json.loads(meta_json or "{}").get("cat_boxes") or []
        if int(item_id) not in preds or not truth:
            continue
        compared += 1
        for t in truth:
            scores.append(max((iou(t, p) for p in preds[int(item_id)]), default=0.0))
    mean = sum(scores) / len(scores) if scores else 0.0
    recall = sum(1 for s in scores if s >= 0.5) / len(scores) if scores else 0.0
    print(
        json.dumps(
            {
                "images": compared,
                "coco_boxes": len(scores),
                "mean_best_iou": round(mean, 3),
                "recall_at_0.5": round(recall, 3),
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
