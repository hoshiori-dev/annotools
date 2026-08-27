import importlib.util
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from captioning import store
from captioning.tools import ToolContext

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def workspace(tmp_path):
    ws = tmp_path / "ws"
    (ws / "data" / "raw" / "coco-cats").mkdir(parents=True)
    db = ws / "data" / "dataset.db"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "init_db.py"), "--db", str(db), "--task", "captioning"],
        check=True,
        capture_output=True,
    )
    Image.new("RGB", (1200, 800), "white").save(ws / "data" / "raw" / "coco-cats" / "a.jpg")
    meta = '{"coco_id": 1}'
    with store.connect(db) as conn:
        conn.execute(
            "INSERT INTO items(uri, media_type, width, height, meta_json) VALUES (?, 'image', 1200, 800, ?)",
            ("data/raw/coco-cats/a.jpg", meta),
        )
        conn.commit()
    return ws, db


def test_tools_preview_record_and_export(workspace, tmp_path):
    ws, db = workspace
    with store.connect(db) as conn:
        run_id = store.start_run(conn, "test-model", {"long": "x"}, {})
    ctx = ToolContext(ws, db, run_id, {"max_width": 768, "max_height": 768, "output_format": "jpeg"})
    data, meta = ctx.look_at_item("data/raw/coco-cats/a.jpg")
    assert meta["output_size"] == [768, 512] and data[:2] == b"\xff\xd8"
    with pytest.raises(ValueError, match="outside the workspace"):
        ctx.look_at_item("../../etc/passwd")
    for variant, text in (
        ("long", "A white cat sits on a sofa."),
        ("medium", "A white cat on a sofa."),
        ("short", "White cat."),
    ):
        assert ctx.record_caption("data/raw/coco-cats/a.jpg", variant, text)["variant"] == variant
    with pytest.raises(ValueError, match="variant"):
        ctx.record_caption("data/raw/coco-cats/a.jpg", "huge", "x")
    assert ctx.record_tags("data/raw/coco-cats/a.jpg", ["Cat", "sofa", "indoor "])["tags"] == ["cat", "indoor", "sofa"]
    out = tmp_path / "captions.jsonl"
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "export_captions.py"), "--db", str(db), "--out", str(out)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    record = json.loads(out.read_text().splitlines()[0])
    assert record == {
        "uri": "data/raw/coco-cats/a.jpg",
        "coco_id": 1,
        "long": "A white cat sits on a sofa.",
        "medium": "A white cat on a sofa.",
        "short": "White cat.",
        "tags": ["cat", "indoor", "sofa"],
    }


def test_download_selects_cat_images():
    spec = importlib.util.spec_from_file_location("download_coco_cats", ROOT / "scripts" / "download_coco_cats.py")
    assert spec and spec.loader
    dl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dl)

    instances = {
        "images": [
            {"id": 1, "file_name": "1.jpg", "width": 10, "height": 10},
            {"id": 2, "file_name": "2.jpg", "width": 10, "height": 10},
        ],
        "annotations": [{"image_id": 1, "category_id": 17}, {"image_id": 2, "category_id": 18}],
    }
    assert [img["id"] for img in dl.cat_images(instances)] == [1]


def test_pipeline_verify_reports_missing(workspace):
    _ws, db = workspace
    with store.connect(db) as conn:
        run_id = store.start_run(conn, "m", {"long": "x"}, {})
        store.record(conn, 1, run_id, "caption", "long", {"text": "x"})
        from captioning.pipeline import verify

        assert verify(conn, 1, run_id) == ["caption:medium", "caption:short", "tag"]
        assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 1
