#!/usr/bin/env python3
"""Export final annotations from an annotools store.

Usage:
    python3 export.py --db dataset.db --format jsonl|csv|parquet|webdataset --out output/ [--name dataset]

One record per item: {"uri", "media_type", "width", "height", "duration", "split", "meta", "annotations":
[{"kind", "key", "label", "confidence", "rounds", "payload": {...}}]}. csv flattens annotations to one row
per annotation; webdataset writes a tar with <key>.json per item where <key> is the first 16 hex
characters of the sha1 of the uri (the media file is referenced by uri, not copied). Items without
final annotations are listed under "skipped" in the JSON summary on stdout. Exit codes: 0 ok, 1 error, 2 bad
arguments (including an unsupported schema version).
"""

import argparse
import csv
import hashlib
import io
import json
import sqlite3
import sys
import tarfile
from pathlib import Path

SCHEMA_VERSION = "1"


def load(conn: sqlite3.Connection) -> tuple[list[dict], list[dict]]:
    items = conn.execute("SELECT id, uri, media_type, width, height, duration, split, meta_json FROM items ORDER BY id").fetchall()
    ann = conn.execute(
        "SELECT item_id, kind, key, label, confidence, rounds, payload_json FROM final_annotations ORDER BY item_id, kind, key"
    ).fetchall()
    by_item: dict[int, list[dict]] = {}
    for item_id, kind, key, label, confidence, rounds, payload in ann:
        by_item.setdefault(item_id, []).append(
            {"kind": kind, "key": key, "label": label, "confidence": confidence, "rounds": rounds, "payload": json.loads(payload)}
        )
    records, skipped = [], []
    for item_id, uri, media_type, width, height, duration, split, meta_json in items:
        if item_id not in by_item:
            skipped.append({"uri": uri, "reason": "no final annotation"})
            continue
        records.append(
            {
                "uri": uri,
                "media_type": media_type,
                "width": width,
                "height": height,
                "duration": duration,
                "split": split,
                "meta": json.loads(meta_json or "{}"),
                "annotations": by_item[item_id],
            }
        )
    return records, skipped


def write(records: list[dict], fmt: str, out_dir: Path, name: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    if fmt == "jsonl":
        path = out_dir / f"{name}.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    elif fmt == "csv":
        path = out_dir / f"{name}.csv"
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(
                ["uri", "media_type", "width", "height", "duration", "split", "meta_json", "kind", "key", "label", "confidence", "rounds", "payload_json"]
            )
            for rec in records:
                for a in rec["annotations"]:
                    writer.writerow(
                        [rec["uri"], rec["media_type"], rec["width"], rec["height"], rec["duration"], rec["split"], json.dumps(rec["meta"]), a["kind"], a["key"], a["label"], a["confidence"], a["rounds"], json.dumps(a["payload"])]
                    )
    elif fmt == "parquet":
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError as exc:
            raise SystemExit("export: error: parquet needs pyarrow (pip install pyarrow)") from exc
        path = out_dir / f"{name}.parquet"
        table = pa.Table.from_pylist([{**rec, "meta": json.dumps(rec["meta"]), "annotations": json.dumps(rec["annotations"])} for rec in records])
        pq.write_table(table, path)
    elif fmt == "webdataset":
        path = out_dir / f"{name}.tar"
        with tarfile.open(path, "w") as tar:
            for rec in records:
                data = json.dumps(rec, ensure_ascii=False).encode("utf-8")
                info = tarfile.TarInfo(f"{hashlib.sha1(rec['uri'].encode('utf-8')).hexdigest()[:16]}.json")
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))
    else:
        raise SystemExit(f"export: error: unknown format {fmt!r}")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--db", required=True)
    parser.add_argument("--format", required=True, choices=["jsonl", "csv", "parquet", "webdataset"])
    parser.add_argument("--out", required=True, help="output directory")
    parser.add_argument("--name", default="dataset")
    args = parser.parse_args(argv)
    if not Path(args.db).is_file():
        print(f"export: error: database not found: {args.db}", file=sys.stderr)
        return 2
    try:
        conn = sqlite3.connect(args.db)
        conn.execute("PRAGMA foreign_keys = ON")
        version = dict(conn.execute("SELECT key, value FROM meta").fetchall()).get("schema_version")
    except sqlite3.Error as exc:
        print(f"export: error: {args.db} is not an annotools store ({exc}); run init_db.py first", file=sys.stderr)
        return 2
    if version != SCHEMA_VERSION:
        print(f"export: error: schema_version {version!r} is not {SCHEMA_VERSION}; run init_db.py or migrate", file=sys.stderr)
        return 2
    records, skipped = load(conn)
    conn.close()
    try:
        path = write(records, args.format, Path(args.out), args.name)
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 1
    print(json.dumps({"path": str(path), "items": len(records), "skipped": skipped}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
