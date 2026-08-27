#!/usr/bin/env python3
"""Digest a GitHub Actions run's failures into one compact JSON object.

Shells out to the gh CLI (must be installed and authenticated) and never
fetches full run logs: it reads only the failed-step logs of failed jobs
and keeps the last N lines per job, so multi-megabyte logs stay out of
agent context.

Usage:
    python3 scripts/run_log_digest.py --repo OWNER/REPO --run-id ID [--tail N]

    --repo    Repository as OWNER/REPO (e.g. octocat/hello-world).
    --run-id  Numeric workflow run id (databaseId from `gh run list`).
    --tail    Log lines to keep per failed job (default 50).

Output: a single JSON object on stdout:
    {"run_id": ..., "status": ..., "conclusion": ...,
     "failed_jobs": [{"name": ..., "job_id": ...,
                      "failed_steps": [...], "log_tail": [...]}]}

Diagnostics go to stderr, never stdout.

Exit codes:
    0  digest produced (a successful run digests to an empty
       failed_jobs list — that is data, not a failure)
    1  gh missing, gh errored, or run not found
    2  bad arguments
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys


def log(message: str) -> None:
    """Print a diagnostic line to stderr."""
    print(message, file=sys.stderr)


def run_gh(args: list) -> "subprocess.CompletedProcess":
    """Run a gh command, exiting 1 with guidance if gh is not installed."""
    try:
        return subprocess.run(
            ["gh", *args], capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        log(
            "error: gh not found — install and authenticate the GitHub CLI "
            "(https://cli.github.com/), or use the MCP column of the skill's "
            "Actions table instead."
        )
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Digest the failed jobs of a GitHub Actions run into one small "
            "JSON object (failed jobs, failed steps, last N log lines each)."
        ),
        epilog=(
            "Exit codes: 0 digest produced (empty failed_jobs on a green "
            "run), 1 gh missing/errored/run not found, 2 bad arguments."
        ),
    )
    parser.add_argument("--repo", required=True, help="repository as OWNER/REPO")
    parser.add_argument(
        "--run-id", required=True, type=int, help="numeric workflow run id"
    )
    parser.add_argument(
        "--tail",
        type=int,
        default=50,
        help="log lines to keep per failed job (default: 50)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    parts = args.repo.split("/")
    if len(parts) != 2 or not all(parts):
        parser.error(
            f"--repo must be OWNER/REPO (got {args.repo!r}), "
            "e.g. --repo octocat/hello-world"
        )
    if args.run_id <= 0:
        parser.error(f"--run-id must be a positive integer (got {args.run_id})")
    if args.tail <= 0:
        parser.error(f"--tail must be a positive integer (got {args.tail})")

    view = run_gh(
        [
            "run",
            "view",
            str(args.run_id),
            "-R",
            args.repo,
            "--json",
            "databaseId,conclusion,status,jobs",
        ]
    )
    if view.returncode != 0:
        log(
            f"error: `gh run view {args.run_id}` failed "
            f"(exit {view.returncode}): {view.stderr.strip()}"
        )
        log(
            f"fix: check that run {args.run_id} exists in {args.repo} "
            "(`gh run list -R " + args.repo + " --limit 20`) and that gh is "
            "authenticated (`gh auth status`)."
        )
        return 1

    try:
        run = json.loads(view.stdout)
    except json.JSONDecodeError as exc:
        log(f"error: could not parse gh JSON output: {exc}")
        log("fix: rerun the command; if it persists, update gh.")
        return 1

    jobs = run.get("jobs") or []
    failed = [j for j in jobs if j.get("conclusion") == "failure"]
    if not failed and run.get("conclusion") == "failure":
        # The run failed but no job reports conclusion=failure (e.g. jobs
        # were cancelled or startup failed); inspect all completed jobs.
        failed = [j for j in jobs if j.get("status") == "completed"]
        log(
            "note: run concluded failure but no job has conclusion=failure; "
            f"falling back to all {len(failed)} completed job(s)."
        )

    failed_jobs = []
    for job in failed:
        job_id = job.get("databaseId")
        name = job.get("name", "")
        steps = job.get("steps") or []
        failed_steps = [
            s.get("name", "") for s in steps if s.get("conclusion") == "failure"
        ]
        log_proc = run_gh(
            ["run", "view", "-R", args.repo, "--job", str(job_id), "--log-failed"]
        )
        if log_proc.returncode != 0:
            log(
                f"note: no failed-step log for job {job_id} ({name}): "
                f"{log_proc.stderr.strip() or 'gh returned no log'}"
            )
            tail = []
        else:
            tail = log_proc.stdout.splitlines()[-args.tail :]
        failed_jobs.append(
            {
                "name": name,
                "job_id": job_id,
                "failed_steps": failed_steps,
                "log_tail": tail,
            }
        )

    digest = {
        "run_id": run.get("databaseId", args.run_id),
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "failed_jobs": failed_jobs,
    }
    json.dump(digest, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
