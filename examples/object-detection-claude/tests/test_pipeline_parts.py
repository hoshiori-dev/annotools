import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from detection import store
from detection.geometry import clean, iou, pixels_to_normalized
from detection.tools import ToolContext

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config" / "default.json").read_text())


@pytest.fixture
def workspace(tmp_path):
    ws = tmp_path / "ws"
    (ws / "data" / "raw" / "coco-cats").mkdir(parents=True)
    db = ws / "data" / "dataset.db"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "init_db.py"), "--db", str(db), "--task", "detection"],
        check=True,
        capture_output=True,
    )
    Image.new("RGB", (1200, 800), "white").save(ws / "data" / "raw" / "coco-cats" / "a.jpg")
    meta = json.dumps({"coco_id": 1, "cat_boxes": [[0.1, 0.1, 0.5, 0.5]]})
    with store.connect(db) as conn:
        conn.execute(
            "INSERT INTO items(uri, media_type, width, height, meta_json) VALUES (?, 'image', 1200, 800, ?)",
            ("data/raw/coco-cats/a.jpg", meta),
        )
        conn.commit()
    return ws, db


def test_geometry():
    meta = {"output_size": [768, 512], "crop": [0, 0, 1, 1]}
    assert pixels_to_normalized([76.8, 51.2, 384, 256], meta) == pytest.approx([0.1, 0.1, 0.5, 0.5])
    assert pixels_to_normalized([384, 256, 76.8, 51.2], meta) == pytest.approx([0.1, 0.1, 0.5, 0.5])  # swapped corners
    assert iou([0, 0, 1, 1], [0, 0, 0.5, 1]) == pytest.approx(0.5)
    kept, rejected = clean(
        [
            {"label": "black_cat", "box": [76.8, 51.2, 384, 256], "confidence": 0.9},
            {"label": "black_cat", "box": [77, 51, 384, 256], "confidence": 0.95},  # duplicate, higher confidence wins
            {"label": "dog", "box": [0, 0, 100, 100]},
            {"label": "other_cat", "box": [0, 0, 5, 5]},
        ],
        meta,
        set(CONFIG["classes"]),
    )
    assert len(kept) == 1 and kept[0]["confidence"] == 0.95
    assert [r.split(":")[0] for r in rejected] == ["1", "2", "3"]


def test_tools_loop_and_export(workspace, tmp_path):
    ws, db = workspace
    with store.connect(db) as conn:
        run_id = store.start_run(conn, "test-model", {"system": "x"}, CONFIG)
    ctx = ToolContext(ws, db, run_id, CONFIG)
    ctx.trial_dir = ws / "data" / "interim" / "trial"
    ctx.trial_dir.mkdir(parents=True)
    data, meta = ctx.look_at_item("data/raw/coco-cats/a.jpg")
    assert meta["output_size"] == [768, 512] and meta["grid"]["columns"] == 10 and data[:2] == b"\xff\xd8"
    boxes = [{"label": "black_cat", "box": [76.8, 51.2, 384, 256], "confidence": 0.9}]
    _, meta = ctx.propose_boxes("data/raw/coco-cats/a.jpg", boxes)
    assert meta["round"] == 1 and meta["kept"] == 1 and list(ctx.trial_dir.iterdir())
    result = ctx.commit_boxes("data/raw/coco-cats/a.jpg", boxes, done=True)
    assert result == {"stored": 1, "status": "final", "rounds": 1, "rejected": []}
    with pytest.raises(ValueError, match="outside the workspace"):
        ctx.look_at_item("../../etc/passwd")
    out = tmp_path / "detections.jsonl"
    export = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "export_detections.py"), "--db", str(db), "--out", str(out)],
        capture_output=True,
        text=True,
    )
    assert export.returncode == 0, export.stderr
    record = json.loads(out.read_text().splitlines()[0])
    assert record["coco_id"] == 1 and record["boxes"][0]["label"] == "black_cat"
    assert record["boxes"][0]["bbox"] == pytest.approx([0.1, 0.1, 0.5, 0.5])
    sanity = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sanity_iou.py"), "--db", str(db)], capture_output=True, text=True
    )
    assert json.loads(sanity.stdout)["mean_best_iou"] == pytest.approx(1.0, abs=0.01)


def test_commit_rules(workspace):
    ws, db = workspace
    with store.connect(db) as conn:
        run_id = store.start_run(conn, "m", {"system": "x"}, CONFIG)
    ctx = ToolContext(ws, db, run_id, CONFIG)
    low = [{"label": "other_cat", "box": [76.8, 51.2, 384, 256], "confidence": 0.3}]
    assert ctx.commit_boxes("data/raw/coco-cats/a.jpg", low, done=True)["status"] == "needs_review"
    assert ctx.commit_boxes("data/raw/coco-cats/a.jpg", [], done=True) == {
        "stored": 0,
        "status": "final",
        "rounds": 0,
        "rejected": [],
    }
    with store.connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM items_pending").fetchone()[0] == 0


def test_download_keeps_cat_boxes():
    spec = importlib.util.spec_from_file_location("download_coco_cats", ROOT / "scripts" / "download_coco_cats.py")
    assert spec and spec.loader
    dl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dl)
    instances = {
        "images": [
            {"id": 1, "file_name": "1.jpg", "width": 200, "height": 100},
            {"id": 2, "file_name": "2.jpg", "width": 10, "height": 10},
        ],
        "annotations": [
            {"image_id": 1, "category_id": 17, "bbox": [20, 10, 80, 40]},
            {"image_id": 2, "category_id": 18, "bbox": [0, 0, 1, 1]},
        ],
    }
    images = dl.cat_images(instances)
    assert [i["id"] for i in images] == [1] and images[0]["cat_boxes"] == [[0.1, 0.1, 0.5, 0.5]]
