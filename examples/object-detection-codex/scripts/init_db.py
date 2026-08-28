"""Create or upgrade an annotools annotation store.

Usage:
    python3 init_db.py --db workspaces/<task>/data/dataset.db --task detection [--schema assets/schema.sql]

Applies the schema (idempotent), sets WAL mode, records the task name, schema version, and the
coordinate convention in `meta`, and creates the `task_annotations` view (final annotations of the
kinds that belong to the task). Prints a JSON summary. Exit codes: 0 ok, 1 error, 2 bad arguments.
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

SCHEMA_VERSION = "1"
CONVENTION = "normalized_xyxy"
TASK_KINDS = {
    "captioning": ("caption", "tag"),
    "detection": ("bbox",),
    "rotated_detection": ("rbox", "polygon"),
    "keypoints": ("keypoints",),
    "segmentation": ("polygon", "mask"),
    "video": ("segment", "bbox"),
    "audio": ("segment",),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--db", required=True, help="path to the SQLite file (created if missing)")
    parser.add_argument("--task", required=True, choices=sorted(TASK_KINDS), help="task family (selects the task view)")
    parser.add_argument("--schema", default=str(Path(__file__).resolve().parent / "schema.sql"))
    args = parser.parse_args(argv)
    schema_path = Path(args.schema)
    if not schema_path.is_file():
        print(f"init_db: error: schema file not found: {schema_path}", file=sys.stderr)
        return 2
    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        try:  # check the version before touching anything
            existing = dict(conn.execute("SELECT key, value FROM meta").fetchall())
        except sqlite3.OperationalError:
            existing = {}
        if existing.get("schema_version", SCHEMA_VERSION) != SCHEMA_VERSION:
            print(
                f"init_db: error: database has schema_version {existing['schema_version']}, "
                f"this script writes {SCHEMA_VERSION}; migrate first",
                file=sys.stderr,
            )
            return 1
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        for key, value in (
            ("task", args.task),
            ("schema_version", SCHEMA_VERSION),
            ("coordinate_convention", CONVENTION),
        ):
            conn.execute(
                "INSERT INTO meta(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
        kinds = ", ".join(f"'{k}'" for k in TASK_KINDS[args.task])
        conn.execute("DROP VIEW IF EXISTS task_annotations")
        conn.execute(f"CREATE VIEW task_annotations AS SELECT * FROM final_annotations WHERE kind IN ({kinds})")
        conn.commit()
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        conn.close()
    except sqlite3.Error as exc:
        print(f"init_db: error: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "db": str(db_path),
                "task": args.task,
                "schema_version": SCHEMA_VERSION,
                "tables": tables,
                "task_view": "task_annotations",
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
