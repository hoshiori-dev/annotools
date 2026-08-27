"""Smoke tests for the scripts shipped inside publishable skills (not covered by ruff/ty)."""

import json
import sqlite3
import subprocess
import sys
import tarfile
from pathlib import Path

STORE = Path(__file__).resolve().parents[1] / "skills" / "sqlite-annotation-store"


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(STORE / "scripts" / script), *args], capture_output=True, text=True, check=False
    )


def seed(db: Path) -> None:
    conn = sqlite3.connect(db)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        "INSERT INTO items(uri, media_type, width, height) VALUES ('a.jpg','image',640,480),('b.jpg','image',640,480)"
    )
    conn.execute("INSERT INTO runs(model, prompt_sha256) VALUES ('m','x'),('m','y')")
    conn.execute(
        "INSERT INTO annotations(item_id, run_id, kind, key, label, payload_json, status)"
        " VALUES (1,1,'caption','long','col',?, 'final')",
        (json.dumps({"text": "a cat", "label": "payload"}),),
    )
    conn.execute(
        "INSERT INTO annotations(item_id, run_id, kind, key, label, payload_json, status)"
        " VALUES (1,2,'bbox','0','cat',?, 'final')",
        (json.dumps({"bbox": [0.1, 0.1, 0.5, 0.5]}),),
    )
    conn.commit()
    conn.close()


def test_init_is_idempotent_and_creates_task_view(tmp_path):
    db = tmp_path / "d.db"
    first = run("init_db.py", "--db", str(db), "--task", "detection")
    second = run("init_db.py", "--db", str(db), "--task", "detection")
    assert first.returncode == 0 and second.returncode == 0, first.stderr + second.stderr
    info = json.loads(second.stdout)
    assert info["task_view"] == "task_annotations" and "annotations" in info["tables"]


def test_init_refuses_other_schema_versions_without_touching_the_db(tmp_path):
    db = tmp_path / "v2.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    conn.execute("INSERT INTO meta VALUES ('schema_version','2')")
    conn.commit()
    conn.close()
    result = run("init_db.py", "--db", str(db), "--task", "detection")
    assert result.returncode == 1 and "migrate first" in result.stderr
    tables = [r[0] for r in sqlite3.connect(db).execute("SELECT name FROM sqlite_master WHERE type='table'")]
    assert tables == ["meta"]


def test_foreign_keys_enforced_when_pragma_set(tmp_path):
    db = tmp_path / "fk.db"
    assert run("init_db.py", "--db", str(db), "--task", "detection").returncode == 0
    conn = sqlite3.connect(db)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        conn.execute("INSERT INTO annotations(item_id, run_id, kind, payload_json) VALUES (999, 999, 'bbox', '{}')")
    except sqlite3.IntegrityError:
        return
    raise AssertionError("foreign key violation was not rejected")


def test_export_keeps_column_label_and_latest_run_per_kind(tmp_path):
    db = tmp_path / "e.db"
    assert run("init_db.py", "--db", str(db), "--task", "captioning").returncode == 0
    seed(db)
    result = run("export.py", "--db", str(db), "--format", "jsonl", "--out", str(tmp_path / "out"))
    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["items"] == 1 and summary["skipped"] == [{"uri": "b.jpg", "reason": "no final annotation"}]
    record = json.loads((tmp_path / "out" / "dataset.jsonl").read_text().splitlines()[0])
    kinds = {a["kind"]: a for a in record["annotations"]}
    assert set(kinds) == {"caption", "bbox"}  # caption from run 1 survives the bbox-only run 2
    assert kinds["caption"]["label"] == "col" and kinds["caption"]["payload"]["label"] == "payload"
    task_rows = sqlite3.connect(db).execute("SELECT kind FROM task_annotations").fetchall()
    assert task_rows == [("caption",)]


def test_export_csv_and_webdataset(tmp_path):
    db = tmp_path / "w.db"
    assert run("init_db.py", "--db", str(db), "--task", "detection").returncode == 0
    seed(db)
    assert run("export.py", "--db", str(db), "--format", "csv", "--out", str(tmp_path / "out")).returncode == 0
    header = (tmp_path / "out" / "dataset.csv").read_text().splitlines()[0]
    assert header.startswith(
        "uri,media_type,width,height,duration,split,meta_json,kind,key,label,confidence,rounds,payload_json"
    )
    assert run("export.py", "--db", str(db), "--format", "webdataset", "--out", str(tmp_path / "out")).returncode == 0
    with tarfile.open(tmp_path / "out" / "dataset.tar") as tar:
        names = tar.getnames()
    assert len(names) == 1 and names[0].endswith(".json") and len(names[0]) == 21


def test_export_rejects_non_store_files(tmp_path):
    junk = tmp_path / "junk.db"
    junk.write_bytes(b"not a database")
    result = run("export.py", "--db", str(junk), "--format", "jsonl", "--out", str(tmp_path))
    assert result.returncode == 2 and "not an annotools store" in result.stderr
    empty = tmp_path / "empty.db"
    sqlite3.connect(empty).close()
    result = run("export.py", "--db", str(empty), "--format", "jsonl", "--out", str(tmp_path))
    assert result.returncode == 2
