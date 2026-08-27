"""Caption pending items with one Claude Agent SDK query per item.

Usage: python -m captioning.pipeline [--limit N] [--trial] [--review] [--config config/default.json]
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from captioning import store
from captioning.tools import ToolContext, build_server

ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = ROOT / "workspaces" / "coco-cats"
DB = WORKSPACE / "data" / "dataset.db"
PROMPTS_DIR = ROOT / "spec" / "prompts"


def load_prompts() -> dict[str, str]:
    return {p.stem: p.read_text(encoding="utf-8").strip() for p in PROMPTS_DIR.glob("*.md")}


def system_prompt(prompts: dict[str, str], config: dict) -> str:
    budgets = config["budgets"]
    return (
        "You caption one image per task using the tools. Steps: 1) call look_at_item with the given uri; "
        "2) write the long caption following these rules:\n" + prompts["long"] + "\n"
        f"3) call record_caption(variant='long'); 4) compress it to at most {budgets['medium_words']} words "
        f"(record_caption variant='medium') and then to at most {budgets['short_words']} words (variant='short') "
        "following:\n"
        + prompts["compress"].replace("{budget}", "<the given budget>").replace("{previous}", "<the previous caption>")
        + "\n"
        "5) produce tags following:\n" + prompts["tags"] + "\ncall record_tags. Finish with the single word DONE."
    )


async def caption_item(ctx: ToolContext, uri: str, config: dict, system: str) -> dict:
    options = ClaudeAgentOptions(
        model=config["model"],
        system_prompt=system,
        cwd=str(ctx.workspace),
        tools=[],
        mcp_servers={"captioning": build_server(ctx)},
        allowed_tools=["mcp__captioning__*"],
        permission_mode="dontAsk",
        max_turns=12,
        max_budget_usd=config.get("max_budget_usd_per_item"),
    )
    started = time.time()
    usage: dict = {"cost_usd": 0.0}
    async for message in query(prompt=f"Caption the item with uri {uri}.", options=options):
        if isinstance(message, ResultMessage):
            usage = {"cost_usd": message.total_cost_usd or 0.0, "subtype": message.subtype, **(message.usage or {})}
    usage["seconds"] = round(time.time() - started, 1)
    return usage


def verify(conn, item_id: int, run_id: int) -> list[str]:
    rows = conn.execute(
        "SELECT kind, key FROM annotations WHERE item_id = ? AND run_id = ? AND status = 'final'", (item_id, run_id)
    ).fetchall()
    have = {(k, key) for k, key in rows}
    missing = [f"caption:{v}" for v in store.VARIANT_KEYS if ("caption", v) not in have]
    if ("tag", "") not in have:
        missing.append("tag")
    return missing


async def run(limit: int | None, trial: bool, config_path: Path) -> int:
    config = json.loads(config_path.read_text())
    prompts = load_prompts()
    system = system_prompt(prompts, config)
    with store.connect(DB) as conn:
        run_id = store.start_run(conn, config["model"], prompts, config)
        items = store.pending_items(conn, limit)
    ctx = ToolContext(WORKSPACE, DB, run_id, config["preview"])
    semaphore = asyncio.Semaphore(1 if trial else config["workers"])
    totals: dict[str, float] = {"items": 0, "cost_usd": 0.0, "needs_review": 0, "seconds": 0.0}
    failures = 0

    async def one(item_id: int, uri: str) -> None:
        nonlocal failures
        async with semaphore:
            try:
                usage = await caption_item(ctx, uri, config, system)
            except Exception as exc:
                usage = {"cost_usd": 0.0, "seconds": 0.0, "error": str(exc)}
            with store.connect(DB) as conn:
                missing = verify(conn, item_id, run_id)
                if missing or "error" in usage:
                    store.record(
                        conn,
                        item_id,
                        run_id,
                        "caption",
                        "long",
                        {"error": usage.get("error", f"missing {missing}")},
                        status="needs_review",
                    )
                    totals["needs_review"] += 1
                    failures += 1
                else:
                    failures = 0
                if trial:
                    rows = conn.execute(
                        "SELECT key, payload_json FROM annotations WHERE item_id = ? AND run_id = ? ORDER BY kind, key",
                        (item_id, run_id),
                    ).fetchall()
                    print(f"\n== {WORKSPACE / uri}")
                    for key, payload in rows:
                        print(f"  {key or 'tags'}: {json.loads(payload)}")
            totals["items"] += 1
            totals["cost_usd"] += float(usage.get("cost_usd") or 0.0)
            totals["seconds"] += float(usage.get("seconds") or 0.0)
            if failures >= config["max_consecutive_failures"]:
                raise RuntimeError(f"{failures} consecutive failures; stopping")

    await asyncio.gather(*(one(i, u) for i, u in items))
    with store.connect(DB) as conn:
        store.finish_run(conn, run_id)
    print(json.dumps({"run_id": run_id, **totals}))
    return 0


def review(sample_rate: float = 0.05) -> int:
    with store.connect(DB) as conn:
        rows = conn.execute(
            "SELECT i.uri, a.key, a.payload_json FROM final_annotations a JOIN items i ON i.id = a.item_id "
            "WHERE a.kind = 'caption' AND (a.item_id * 2654435761) % 100 < ? ORDER BY a.item_id, a.key",
            (int(sample_rate * 100),),
        ).fetchall()
    for uri, key, payload in rows:
        print(f"{WORKSPACE / uri}\t{key}\t{json.loads(payload)['text']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Caption pending COCO cat images.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--trial", action="store_true", help="sequential; print paths and captions for review")
    parser.add_argument("--review", action="store_true", help="print a 5%% sample of final captions")
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "default.json")
    args = parser.parse_args(argv)
    if args.review:
        return review()
    return asyncio.run(run(args.limit, args.trial, args.config))


if __name__ == "__main__":
    sys.exit(main())
