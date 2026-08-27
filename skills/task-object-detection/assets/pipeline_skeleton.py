"""Detection pipeline skeleton (SDK-agnostic): grid -> propose -> verify -> correct (<= N rounds) -> commit."""

import asyncio
import json
import sqlite3
from pathlib import Path

from build_preview_call import to_normalized  # from the localization-annotation-guide skill assets
from vision_tools import VisionTools  # from the agent-vision-tools skill

WORKSPACE = Path("workspaces/<task>")
DB = WORKSPACE / "data" / "dataset.db"
RUN_ID = 1
MAX_ROUNDS = 3  # confirmed with the user in the interview
CONVENTION = "pixels"  # or "gemini"; from config/
CONFIDENCE_FLOOR = 0.5


async def call_model(system: str, user_parts: list) -> dict:  # pragma: no cover - SDK specific
    raise NotImplementedError("send system + user_parts; return the parsed JSON object")


def clean(boxes: list[dict], meta: dict, classes: set[str]) -> list[dict]:
    out = []
    for b in boxes:
        if b.get("label") not in classes:
            continue
        x0, y0, x1, y1 = to_normalized(b["box"], CONVENTION, meta)
        if x1 - x0 <= 0 or y1 - y0 <= 0:
            continue
        out.append({"bbox": [x0, y0, x1, y1], "label": b["label"], "confidence": float(b.get("confidence", 0.5))})
    return out


async def detect_item(conn: sqlite3.Connection, vision: VisionTools, item_id: int, uri: str, prompts: dict, classes: set[str]) -> None:
    image, meta = vision.look_at_item(uri, grid={})
    proposal = await call_model(prompts["propose"], [image, f"Image id: {item_id}; shown size: {meta['output_size']}"])
    boxes = clean(proposal.get("boxes", []), meta, classes)
    rounds, done = 0, False
    while rounds < MAX_ROUNDS and boxes and not done:
        overlay, _ = vision.look_at_annotations(uri, bboxes=[{**b, "label": f"{i}:{b['label']}"} for i, b in enumerate(boxes)])
        answer = await call_model(prompts["propose"] + prompts["correct"], [overlay])
        rounds += 1
        done = bool(answer.get("done"))
        for edit in answer.get("edits", []):
            index = edit["index"]
            if edit.get("box") is None:
                boxes[index] = None
            elif 0 <= index < len(boxes):
                boxes[index]["bbox"] = to_normalized(edit["box"], CONVENTION, meta)
        boxes = [b for b in boxes if b] + clean(answer.get("add", []), meta, classes)
    status = "final" if done or all(b["confidence"] >= CONFIDENCE_FLOOR for b in boxes) else "needs_review"
    for index, b in enumerate(boxes):
        conn.execute(
            "INSERT INTO annotations(item_id, run_id, kind, key, label, payload_json, confidence, rounds, status) VALUES (?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(item_id, run_id, kind, key) DO UPDATE SET label=excluded.label, payload_json=excluded.payload_json, "
            "confidence=excluded.confidence, rounds=excluded.rounds, status=excluded.status",
            (item_id, RUN_ID, "bbox", str(index), b["label"], json.dumps({"bbox": b["bbox"]}), b["confidence"], rounds, status),
        )
    conn.commit()


async def main(workers: int = 4) -> None:
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    vision = VisionTools(WORKSPACE, max_width=768, max_height=768)
    prompts = {name: (Path("spec/prompts") / f"{name}.md").read_text() for name in ("propose", "correct")}
    classes = set(json.loads(Path("config/classes.json").read_text()))
    pending = conn.execute("SELECT id, uri FROM items_pending").fetchall()
    semaphore = asyncio.Semaphore(workers)

    async def guarded(item_id: int, uri: str) -> None:
        async with semaphore:
            await detect_item(conn, vision, item_id, uri, prompts, classes)

    await asyncio.gather(*(guarded(i, u) for i, u in pending))


if __name__ == "__main__":
    asyncio.run(main())
