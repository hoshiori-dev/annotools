"""Caption pending items with one Codex SDK thread per item.

Usage: python -m captioning.pipeline [--limit N] [--trial] [--review] [--config config/default.json]
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from captioning import store
from captioning.tools import ToolContext

ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = ROOT / "workspaces" / "coco-cats"
DB = WORKSPACE / "data" / "dataset.db"
PROMPTS_DIR = ROOT / "spec" / "prompts"
TOKEN_KEYS = ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")


def load_prompts() -> dict[str, str]:
    return {p.stem: p.read_text(encoding="utf-8").strip() for p in PROMPTS_DIR.glob("*.md")}


def system_prompt(prompts: dict[str, str], config: dict) -> str:
    budgets = config["budgets"]
    compress = (
        prompts["compress"].replace("{budget}", "<the given budget>").replace("{previous}", "<the previous caption>")
    )
    return (
        "You caption one image per task using the tools. Steps: 1) call look_at_item with the given uri; "
        "2) write the long caption following these rules:\n" + prompts["long"] + "\n"
        f"3) call record_caption(variant='long'); 4) compress it to at most {budgets['medium_words']} words "
        f"(record_caption variant='medium') and then to at most {budgets['short_words']} words (variant='short') "
        "following:\n" + compress + "\n"
        "5) produce tags following:\n" + prompts["tags"] + "\ncall record_tags. Finish with the single word DONE."
    )


def mcp_config(ctx: ToolContext) -> dict:
    """Codex config override registering the tools server (same shape as .codex/config.toml)."""
    args = [
        "-m",
        "captioning.tools",
        "--workspace",
        str(ctx.workspace),
        "--db",
        str(ctx.db),
        "--run-id",
        str(ctx.run_id),
        "--preview",
        json.dumps(ctx.preview_cfg),
    ]
    return {"mcp_servers": {"captioning": {"command": sys.executable, "args": args}}}


async def caption_item(ctx: ToolContext, uri: str, config: dict, system: str) -> dict:
    from openai_codex import Codex, Sandbox  # imported here so the tests do not need the SDK runtime

    started = time.time()

    def run_sync() -> dict:
        with Codex() as codex:
            thread = codex.thread_start(
                model=config["model"],
                sandbox=Sandbox.read_only,
                cwd=str(ctx.workspace),
                config=mcp_config(ctx),
                base_instructions=system,
            )
            result = thread.run(f"Caption the item with uri {uri}.", effort=config.get("effort"))
        usage = getattr(result, "usage", None)
        usage_dict = usage if isinstance(usage, dict) else (vars(usage) if usage is not None else {})
        return {"final_response": result.final_response, **usage_dict}

    usage = await asyncio.to_thread(run_sync)
    usage["cost_usd"] = 0.0  # the Codex SDK reports tokens, not cost; fill the README from the provider dashboard
    usage["seconds"] = round(time.time() - started, 1)
    return usage


def verify(conn, item_id: int, run_id: int, budgets: dict[str, int] | None = None) -> list[str]:
    """Return what keeps the item from being accepted: missing variants/tags and captions over their word budget."""
    rows = conn.execute(
        "SELECT kind, key, payload_json FROM annotations WHERE item_id = ? AND run_id = ? AND status = 'final'",
        (item_id, run_id),
    ).fetchall()
    have = {(k, key): json.loads(payload) for k, key, payload in rows}
    problems = [f"caption:{v} missing" for v in store.VARIANT_KEYS if ("caption", v) not in have]
    if ("tag", "") not in have:
        problems.append("tag missing")
    for variant, limit in (budgets or {}).items():
        text = have.get(("caption", variant), {}).get("text", "")
        if text and len(text.split()) > limit:
            problems.append(f"caption:{variant} over budget ({len(text.split())} > {limit} words)")
    return problems


def fail_item(conn, item_id: int, run_id: int, reason: str) -> None:
    """Demote every row of the item in this run and add an error row: nothing is overwritten, the item stays pending."""
    conn.execute("UPDATE annotations SET status = 'needs_review' WHERE item_id = ? AND run_id = ?", (item_id, run_id))
    conn.commit()
    store.record(conn, item_id, run_id, "caption", "error", {"error": reason}, status="needs_review")


def print_trial(conn, item_id: int, run_id: int, uri: str) -> None:
    rows = conn.execute(
        "SELECT key, payload_json FROM annotations WHERE item_id = ? AND run_id = ? ORDER BY kind, key",
        (item_id, run_id),
    ).fetchall()
    print(f"\n== {WORKSPACE / uri}")
    for key, payload in rows:
        print(f"  {key or 'tags'}: {json.loads(payload)}")


async def run(limit: int | None, trial: bool, config_path: Path) -> int:
    config = json.loads(config_path.read_text())
    prompts = load_prompts()
    system = system_prompt(prompts, config)
    with store.connect(DB) as conn:
        run_id = store.start_run(conn, config["model"], prompts, config)
        items = store.pending_items(conn, limit)
    ctx = ToolContext(WORKSPACE, DB, run_id, config["preview"])
    semaphore = asyncio.Semaphore(1 if trial else config["workers"])
    budgets = {"medium": config["budgets"]["medium_words"], "short": config["budgets"]["short_words"]}
    totals: dict[str, float] = {"items": 0, "needs_review": 0, "cost_usd": 0.0, "seconds": 0.0}
    totals.update(dict.fromkeys(TOKEN_KEYS, 0))
    failures = 0
    stop = asyncio.Event()

    async def one(item_id: int, uri: str) -> None:
        nonlocal failures
        async with semaphore:
            if stop.is_set():
                return
            try:
                usage = await caption_item(ctx, uri, config, system)
            except Exception as exc:
                usage = {"cost_usd": 0.0, "seconds": 0.0, "error": str(exc)}
            with store.connect(DB) as conn:
                problems = verify(conn, item_id, run_id, budgets)
                if problems or "error" in usage:
                    fail_item(conn, item_id, run_id, str(usage.get("error") or "; ".join(problems)))
                    totals["needs_review"] += 1
                    failures += 1
                else:
                    failures = 0
                if trial:
                    print_trial(conn, item_id, run_id, uri)
            totals["items"] += 1
            totals["cost_usd"] += float(usage.get("cost_usd") or 0.0)
            totals["seconds"] += float(usage.get("seconds") or 0.0)
            for key in TOKEN_KEYS:
                totals[key] += int(usage.get(key) or 0)
            if failures >= config["max_failures"] and not stop.is_set():
                stop.set()
                print(f"stopping: {failures} failures in a row (max_failures)", file=sys.stderr)

    await asyncio.gather(*(one(i, u) for i, u in items))
    with store.connect(DB) as conn:
        store.finish_run(conn, run_id)
    print(json.dumps({"run_id": run_id, "stopped_early": stop.is_set(), **totals}))
    return 1 if stop.is_set() else 0


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
