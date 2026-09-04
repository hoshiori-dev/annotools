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
        check=False,
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

        assert verify(conn, 1, run_id) == ["caption:medium missing", "caption:short missing", "tag missing"]
        assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 1


def test_system_prompt_assembly():
    from captioning.pipeline import load_prompts, system_prompt

    config = json.loads((ROOT / "config" / "default.json").read_text())
    text = system_prompt(load_prompts(), config)
    assert "{budget}" not in text and "{previous}" not in text
    assert f"at most {config['budgets']['medium_words']} words" in text
    assert "record_tags" in text and "DONE" in text


def test_failure_keeps_good_captions_and_item_pending(workspace):
    from captioning.pipeline import fail_item, verify

    _ws, db = workspace
    with store.connect(db) as conn:
        run_id = store.start_run(conn, "m", {"long": "x"}, {})
        store.record(conn, 1, run_id, "caption", "long", {"text": "a long caption"})
        fail_item(conn, 1, run_id, "tags failed")
        rows = dict(
            conn.execute("SELECT key, status FROM annotations WHERE item_id = 1 AND run_id = ?", (run_id,)).fetchall()
        )
        assert rows == {"long": "needs_review", "error": "needs_review"}
        assert (
            conn.execute("SELECT payload_json FROM annotations WHERE key = 'long'").fetchone()[0]
            == '{"text": "a long caption"}'
        )
        assert conn.execute("SELECT COUNT(*) FROM items_pending").fetchone()[0] == 1
        store.record(conn, 1, run_id, "caption", "medium", {"text": " ".join(["w"] * 40)})
        assert any("over budget" in p for p in verify(conn, 1, run_id, {"medium": 25}))


async def test_caption_item_keeps_the_cost_of_a_budget_error(workspace, monkeypatch):
    from claude_agent_sdk import ResultError, ResultMessage

    from captioning import pipeline

    ws, db = workspace
    config = json.loads((ROOT / "config" / "default.json").read_text())
    ctx = ToolContext(ws, db, 1, config["preview"])

    async def failing_query(prompt, options):
        yield ResultMessage(
            subtype="error_max_budget_usd",
            duration_ms=1,
            duration_api_ms=1,
            is_error=True,
            num_turns=1,
            session_id="s",
            total_cost_usd=0.16,
            usage={"cache_read_input_tokens": 18000},
        )
        raise ResultError("Reached maximum budget", exit_code=1)

    monkeypatch.setattr(pipeline, "query", failing_query)
    usage = await pipeline.caption_item(ctx, "data/raw/coco-cats/a.jpg", config, "system")
    assert usage["error"].startswith("Reached maximum budget") and usage["subtype"] == "error_max_budget_usd"
    assert usage["cost_usd"] == 0.16 and usage["cache_read_input_tokens"] == 18000


BUDGET_ERROR = {"cost_usd": 0.2503, "subtype": "error_max_budget_usd", "error": "Reached maximum budget ($0.25)"}


def complete_item(conn, run_id: int) -> None:
    for variant, text in (("long", "a long caption"), ("medium", "a medium caption"), ("short", "short")):
        store.record(conn, 1, run_id, "caption", variant, {"text": text})
    store.record(conn, 1, run_id, "tag", "", {"tags": ["cat", "indoor", "sofa"]})


def test_budget_stop_after_a_complete_item_keeps_the_captions(workspace, tmp_path):
    from captioning.pipeline import settle, verify

    _ws, db = workspace
    with store.connect(db) as conn:
        run_id = store.start_run(conn, "m", {"long": "x"}, {})
        complete_item(conn, run_id)
        assert verify(conn, 1, run_id) == []
        assert settle(conn, 1, run_id, [], dict(BUDGET_ERROR)) == ("final", True)
        rows = dict(
            conn.execute("SELECT key, status FROM annotations WHERE item_id = 1 AND run_id = ?", (run_id,)).fetchall()
        )
        assert rows == {"long": "final", "medium": "final", "short": "final", "": "final", "budget_stop": "final"}
        assert conn.execute("SELECT COUNT(*) FROM items_pending").fetchone()[0] == 0
    out = tmp_path / "captions.jsonl"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "export_captions.py"), "--db", str(db), "--out", str(out)],
        check=True,
        capture_output=True,
    )
    record = json.loads(out.read_text().strip())  # the budget_stop row does not reach the export
    assert set(record) == {"uri", "coco_id", "long", "medium", "short", "tags"}
    assert record["tags"] == ["cat", "indoor", "sofa"]


def test_budget_stop_on_an_incomplete_item_is_still_needs_review(workspace):
    from captioning.pipeline import settle, verify

    _ws, db = workspace
    with store.connect(db) as conn:
        run_id = store.start_run(conn, "m", {"long": "x"}, {})
        store.record(conn, 1, run_id, "caption", "long", {"text": "a long caption"})
        assert settle(conn, 1, run_id, verify(conn, 1, run_id), dict(BUDGET_ERROR)) == ("needs_review", False)
        rows = dict(
            conn.execute("SELECT key, status FROM annotations WHERE item_id = 1 AND run_id = ?", (run_id,)).fetchall()
        )
        assert rows == {"long": "needs_review", "error": "needs_review"}
        assert conn.execute("SELECT COUNT(*) FROM items_pending").fetchone()[0] == 1
