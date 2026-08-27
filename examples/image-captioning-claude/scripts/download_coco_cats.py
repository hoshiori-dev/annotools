#!/usr/bin/env python3
"""Download the COCO 2017 val images that contain a cat and register them in the workspace store.

Usage:
    python scripts/download_coco_cats.py --workspace workspaces/coco-cats [--limit N] [--annotations PATH]

Steps: fetch annotations_trainval2017.zip (241 MB, cached under data/interim/), read
instances_val2017.json from it without extracting the rest, select images whose annotations include
category `cat` (id 17), download only those images into data/raw/coco-cats/, and insert `items` rows
(file pointers only) into data/dataset.db. Idempotent: existing files are skipped and items are
INSERT OR IGNORE. Raw data is never modified by any other script.
Exit codes: 0 ok, 1 network or database error, 2 bad arguments.
"""

import argparse
import io
import json
import sqlite3
import sys
import urllib.request
import zipfile
from pathlib import Path

ANNOTATIONS_URL = "https://images.cocodataset.org/annotations/annotations_trainval2017.zip"
IMAGE_URL = "https://images.cocodataset.org/val2017/{file_name}"
CAT_CATEGORY_ID = 17


def fetch(url: str, dest: Path) -> Path:
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as response, tmp.open("wb") as fh:
        while chunk := response.read(1 << 20):
            fh.write(chunk)
    tmp.replace(dest)
    return dest


def load_instances(zip_path: Path) -> dict:
    with zipfile.ZipFile(zip_path) as archive, archive.open("annotations/instances_val2017.json") as fh:
        return json.load(io.TextIOWrapper(fh, encoding="utf-8"))


def cat_images(instances: dict) -> list[dict]:
    cat_ids = {a["image_id"] for a in instances["annotations"] if a["category_id"] == CAT_CATEGORY_ID}
    return sorted((img for img in instances["images"] if img["id"] in cat_ids), key=lambda i: i["id"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--workspace", default="workspaces/coco-cats")
    parser.add_argument("--limit", type=int, default=None, help="only the first N cat images (for trials)")
    parser.add_argument("--annotations", default=None, help="reuse an already downloaded annotations zip")
    args = parser.parse_args(argv)
    workspace = Path(args.workspace)
    raw = workspace / "data" / "raw" / "coco-cats"
    db = workspace / "data" / "dataset.db"
    if not db.exists():
        print(f"download: error: {db} not found; run `just init-db` first", file=sys.stderr)
        return 2
    try:
        zip_path = (
            Path(args.annotations)
            if args.annotations
            else fetch(ANNOTATIONS_URL, workspace / "data" / "interim" / "annotations_trainval2017.zip")
        )
        images = cat_images(load_instances(zip_path))
        if args.limit:
            images = images[: args.limit]
        conn = sqlite3.connect(db)
        conn.execute("PRAGMA foreign_keys = ON")
        downloaded = 0
        for img in images:
            path = fetch(IMAGE_URL.format(file_name=img["file_name"]), raw / img["file_name"])
            downloaded += 1
            conn.execute(
                "INSERT OR IGNORE INTO items(uri, media_type, width, height, meta_json) VALUES (?, 'image', ?, ?, ?)",
                (str(path.relative_to(workspace)), img["width"], img["height"], json.dumps({"coco_id": img["id"]})),
            )
        conn.commit()
        total = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        conn.close()
    except (OSError, sqlite3.Error, KeyError, zipfile.BadZipFile) as exc:
        print(f"download: error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"cat_images": len(images), "downloaded": downloaded, "items_in_db": total, "raw": str(raw)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
