"""SQLite access for the captioning pipeline (schema from the sqlite-annotation-store skill)."""

import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path

VARIANT_KEYS = ("long", "medium", "short")


def connect(db: Path) -> closing[sqlite3.Connection]:
    """Open a connection (30 s busy timeout, foreign keys on) that closes at the end of a ``with`` block."""
    conn = sqlite3.connect(db, timeout=30)
    conn.execute("PRAGMA foreign_keys = ON")
    return closing(conn)


def start_run(conn: sqlite3.Connection, model: str, prompts: dict[str, str], config: dict) -> int:
    digest = hashlib.sha256("\n".join(prompts[k] for k in sorted(prompts)).encode("utf-8")).hexdigest()
    cur = conn.execute(
        "INSERT INTO runs(model, prompt_sha256, config_json) VALUES (?, ?, ?)", (model, digest, json.dumps(config))
    )
    conn.commit()
    if cur.lastrowid is None:
        raise RuntimeError("run insert returned no id")
    return int(cur.lastrowid)


def finish_run(conn: sqlite3.Connection, run_id: int) -> None:
    conn.execute("UPDATE runs SET finished_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = ?", (run_id,))
    conn.commit()


def pending_items(conn: sqlite3.Connection, limit: int | None = None) -> list[tuple[int, str]]:
    sql = "SELECT id, uri FROM items_pending ORDER BY id"
    if limit is not None:
        sql += f" LIMIT {int(limit)}"
    return [(int(i), u) for i, u in conn.execute(sql).fetchall()]


def record(
    conn: sqlite3.Connection, item_id: int, run_id: int, kind: str, key: str, payload: dict, status: str = "final"
) -> int:
    cur = conn.execute(
        "INSERT INTO annotations(item_id, run_id, kind, key, payload_json, status) VALUES (?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(item_id, run_id, kind, key) DO UPDATE SET payload_json = excluded.payload_json, "
        "status = excluded.status "
        "RETURNING id",
        (item_id, run_id, kind, key, json.dumps(payload), status),
    )
    annotation_id = int(cur.fetchone()[0])
    conn.commit()
    return annotation_id


def item_id_for(conn: sqlite3.Connection, uri: str) -> int | None:
    row = conn.execute("SELECT id FROM items WHERE uri = ?", (uri,)).fetchone()
    return int(row[0]) if row else None
