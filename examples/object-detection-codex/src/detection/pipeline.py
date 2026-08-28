"""Detect cats on pending items with one Codex SDK thread per item.

Usage: python -m detection.pipeline [--limit N] [--trial] [--config config/default.json]
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from detection import store
from detection.tools import ToolContext

ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = ROOT / "workspaces" / "coco-cats"
DB = WORKSPACE / "data" / "dataset.db"
SYSTEM_PROMPT = ROOT / "spec" / "prompts" / "system.md"
TOKEN_KEYS = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "total_tokens")


def system_prompt(config: dict) -> str:
    grid = config["grid"]
    return (
        SYSTEM_PROMPT.read_text(encoding="utf-8")
        .replace("{max_rounds}", str(config["max_rounds"]))
        .replace("{grid}", f"{grid['columns']}x{grid['rows']}")
        .replace("{max_boxes}", str(config.get("max_boxes", 20)))
    )


def flatten_usage(usage: object) -> dict[str, int]:
    """Flatten a Codex ``ThreadTokenUsage`` (``usage.total`` breakdown) into the summary's token keys."""
    total = getattr(usage, "total", None)
    if total is None and isinstance(usage, dict):
        total = usage.get("total")
    if total is None:
        return {}
    read = total.get if isinstance(total, dict) else lambda k, d=None: getattr(total, k, d)
    return {key: int(read(key, 0) or 0) for key in TOKEN_KEYS}


def mcp_config(ctx: ToolContext) -> dict:
    """Codex config override registering the tools server (same shape as .codex/config.toml)."""
    args = [
        "-m",
        "detection.tools",
        "--workspace",
        str(ctx.workspace),
        "--db",
        str(ctx.db),
        "--run-id",
        str(ctx.run_id),
        "--config",
        json.dumps(ctx.config),
    ]
    if ctx.trial_dir:
        args += ["--trial-dir", str(ctx.trial_dir)]
    # approve: Codex gates MCP tool calls behind approval by default, and deny_all (approval_policy "never")
    # would reject every call; this is our own server, so its tools are pre-approved.
    return {
        "mcp_servers": {
            "detection": {"command": sys.executable, "args": args, "default_tools_approval_mode": "approve"}
        }
    }


async def detect_item(ctx: ToolContext, uri: str, config: dict, system: str) -> dict:
    from openai_codex import ApprovalMode, Codex, Sandbox  # imported here so the tests do not need the SDK runtime

    started = time.time()

    def run_sync() -> dict:
        with Codex() as codex:
            thread = codex.thread_start(
                model=config["model"],
                sandbox=Sandbox.read_only,
                approval_mode=ApprovalMode.deny_all,  # unattended; MCP tools are approved in mcp_config()
                cwd=str(ctx.workspace),
                config=mcp_config(ctx),
                base_instructions=system,
            )
            result = thread.run(f"Detect the cats in the item with uri {uri}.", effort=config.get("effort"))
        return {"final_response": result.final_response, **flatten_usage(getattr(result, "usage", None))}

    try:
        usage = await asyncio.wait_for(asyncio.to_thread(run_sync), timeout=config.get("max_seconds_per_item"))
    except TimeoutError as exc:
        raise RuntimeError(f"item exceeded max_seconds_per_item={config.get('max_seconds_per_item')}") from exc
    usage["cost_usd"] = 0.0  # the Codex SDK reports tokens, not cost; fill the README from the provider dashboard
    usage["seconds"] = round(time.time() - started, 1)
    return usage


def committed(conn, item_id: int, run_id: int) -> tuple[int, str | None, int]:
    """(box count, aggregate status, rounds) for the item in this run; needs_review if any row is."""
    rows = conn.execute(
        "SELECT kind, status, rounds FROM annotations WHERE item_id = ? AND run_id = ?", (item_id, run_id)
    ).fetchall()
    if not rows:
        return 0, None, 0
    boxes = sum(1 for k, _, _ in rows if k == "bbox")
    status = "needs_review" if any(s == "needs_review" for _, s, _ in rows) else "final"
    rounds = max(r for _, _, r in rows)
    return boxes, status, rounds


async def run(limit: int | None, trial: bool, config_path: Path) -> int:
    config = json.loads(config_path.read_text())
    system = system_prompt(config)
    with store.connect(DB) as conn:
        run_id = store.start_run(conn, config["model"], {"system": system}, config)
        items = store.pending_items(conn, limit)
    ctx = ToolContext(WORKSPACE, DB, run_id, config)
    if trial:
        ctx.trial_dir = WORKSPACE / "data" / "interim" / "trial"
        ctx.trial_dir.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(1 if trial else config["workers"])
    totals: dict[str, float] = {"items": 0, "cost_usd": 0.0, "needs_review": 0, "seconds": 0.0, "rounds": 0}
    totals.update(dict.fromkeys(TOKEN_KEYS, 0))
    failures = 0
    stop = asyncio.Event()

    async def one(item_id: int, uri: str) -> None:
        nonlocal failures
        async with semaphore:
            if stop.is_set():
                return
            try:
                usage = await detect_item(ctx, uri, config, system)
            except Exception as exc:
                usage = {"cost_usd": 0.0, "seconds": 0.0, "error": str(exc)}
            with store.connect(DB) as conn:
                _boxes, status, rounds = committed(conn, item_id, run_id)
                if status is None or "error" in usage:
                    store.record(
                        conn,
                        item_id,
                        run_id,
                        "tag",
                        "error",
                        {"tags": ["error"], "error": usage.get("error", "nothing committed")},
                        "needs_review",
                    )
                    conn.execute(
                        "UPDATE annotations SET status = 'needs_review' WHERE item_id = ? AND run_id = ?",
                        (item_id, run_id),
                    )
                    conn.commit()
                    status = "needs_review"
                if status == "needs_review":
                    totals["needs_review"] += 1
                    failures += 1
                else:
                    failures = 0
                if trial:
                    rows = conn.execute(
                        "SELECT key, label, confidence, payload_json FROM annotations "
                        "WHERE item_id = ? AND run_id = ? AND kind = 'bbox' ORDER BY CAST(key AS INTEGER)",
                        (item_id, run_id),
                    ).fetchall()
                    print(f"\n== {WORKSPACE / uri}  status={status} rounds={rounds}  overlays: {ctx.trial_dir}")
                    for key, label, confidence, payload in rows:
                        print(f"  [{key}] {label} conf={confidence} bbox={json.loads(payload)['bbox']}")
            totals["items"] += 1
            totals["rounds"] += ctx.rounds.get(uri, rounds)
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
    totals["mean_rounds"] = round(totals["rounds"] / totals["items"], 2) if totals["items"] else 0.0
    print(json.dumps({"run_id": run_id, "stopped_early": stop.is_set(), **totals}))
    return 1 if stop.is_set() else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Box cats on pending COCO images.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--trial", action="store_true", help="sequential; save overlays and print boxes for review")
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "default.json")
    args = parser.parse_args(argv)
    return asyncio.run(run(args.limit, args.trial, args.config))


if __name__ == "__main__":
    sys.exit(main())
