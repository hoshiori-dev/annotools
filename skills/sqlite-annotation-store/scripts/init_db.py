#!/usr/bin/env python3
"""Create or upgrade an annotools annotation store.

Usage:
    python3 init_db.py --db workspaces/<task>/data/dataset.db --task detection [--schema assets/schema.sql]

Applies the schema (idempotent), sets WAL mode, and records the task name, schema version, and the
coordinate convention in `meta`. Prints a JSON summary. Exit codes: 0 ok, 1 error, 2 bad arguments.
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

SCHEMA_VERSION = "1"
CONVENTION = "normalized_xyxy"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--db", required=True, help="path to the SQLite file (created if missing)")
    parser.add_argument("--task", required=True, help="task family, e.g. captioning, detection, keypoints")
    parser.add_argument("--schema", default=str(Path(__file__).resolve().parent.parent / "assets" / "schema.sql"))
    args = parser.parse_args(argv)
    schema_path = Path(args.schema)
    if not schema_path.is_file():
        print(f"init_db: error: schema file not found: {schema_path}", file=sys.stderr)
        return 2
    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        conn = sqlite3.connect(db_path)
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        existing = dict(conn.execute("SELECT key, value FROM meta").fetchall())
        if existing.get("schema_version", SCHEMA_VERSION) != SCHEMA_VERSION:
            print(
                f"init_db: error: database has schema_version {existing['schema_version']}, this script writes {SCHEMA_VERSION}; migrate first",
                file=sys.stderr,
            )
            return 1
        for key, value in (("task", args.task), ("schema_version", SCHEMA_VERSION), ("coordinate_convention", CONVENTION)):
            conn.execute("INSERT INTO meta(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))
        conn.commit()
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        conn.close()
    except sqlite3.Error as exc:
        print(f"init_db: error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"db": str(db_path), "task": args.task, "schema_version": SCHEMA_VERSION, "tables": tables}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
