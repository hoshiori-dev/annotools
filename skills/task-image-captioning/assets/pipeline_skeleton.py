"""Linear captioning pipeline skeleton (SDK-agnostic). Fill `call_model` with the SDK client.

Per item: preview (annotools) -> long caption -> compress to medium and short -> tags -> 4 writes.
"""

import asyncio
import json
import sqlite3
from pathlib import Path

from vision_tools import VisionTools  # from the agent-vision-tools skill

WORKSPACE = Path("workspaces/<task>")
DB = WORKSPACE / "data" / "dataset.db"
RUN_ID = 1  # created by the pipeline start-up (runs table)
VARIANTS = {"medium": 40, "short": 15}  # token budgets from spec/task.md


async def call_model(system: str, user_parts: list) -> str:  # pragma: no cover - SDK specific
    raise NotImplementedError("send system + user_parts (image bytes + text) with the SDK; return text")


def record(conn: sqlite3.Connection, item_id: int, kind: str, key: str, payload: dict, status: str = "final") -> None:
    conn.execute(
        "INSERT INTO annotations(item_id, run_id, kind, key, payload_json, status) VALUES (?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(item_id, run_id, kind, key) DO UPDATE SET payload_json = excluded.payload_json, status = excluded.status",
        (item_id, RUN_ID, kind, key, json.dumps(payload), status),
    )
    conn.commit()


async def caption_item(conn: sqlite3.Connection, vision: VisionTools, item_id: int, uri: str, prompts: dict) -> None:
    try:
        image, _meta = vision.look_at_item(uri)
        long = await call_model(prompts["long"], [image, f"Image id: {item_id}"])
        record(conn, item_id, "caption", "long", {"text": long})
        previous = long
        for key, budget in VARIANTS.items():
            previous = await call_model(prompts["compress"].replace("<budget>", str(budget)), [previous])
            record(conn, item_id, "caption", key, {"text": previous})
        tags = json.loads(await call_model(prompts["tags"], [image, f"Image id: {item_id}"]))
        record(conn, item_id, "tag", "", {"tags": tags})
    except Exception as exc:  # noqa: BLE001 - every failure becomes a reviewable row
        record(conn, item_id, "caption", "long", {"error": str(exc)}, status="needs_review")


async def main(workers: int = 8) -> None:
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    vision = VisionTools(WORKSPACE, max_width=768, max_height=768)
    prompts = {name: (Path("spec/prompts") / f"{name}.md").read_text() for name in ("long", "compress", "tags")}
    pending = conn.execute("SELECT id, uri FROM items_pending").fetchall()
    semaphore = asyncio.Semaphore(workers)

    async def guarded(item_id: int, uri: str) -> None:
        async with semaphore:
            await caption_item(conn, vision, item_id, uri, prompts)

    await asyncio.gather(*(guarded(i, u) for i, u in pending))


if __name__ == "__main__":
    asyncio.run(main())
