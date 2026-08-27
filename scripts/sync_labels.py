#!/usr/bin/env python3
"""Sync a GitHub repository's labels to a JSON taxonomy file via the gh CLI.

Reads the desired labels from a JSON array of {"name", "color",
"description"} objects, compares them with the labels currently in the
repository, and prints the resulting plan as JSON to stdout. Dry-run by
default: nothing changes without --apply. Idempotent: re-running after a
successful apply yields an all-skip plan.

Exit codes: 0 plan printed or applied cleanly, 1 gh missing or a gh
command failed, 2 bad arguments or an invalid labels file.
"""

import argparse
import json
import re
import subprocess
import sys

HEX_COLOR = re.compile(r"^[0-9a-f]{6}$")
REPO_SLUG = re.compile(r"^[^/\s]+/[^/\s]+$")


def fail(code, message):
    print(f"sync_labels: error: {message}", file=sys.stderr)
    sys.exit(code)


def run_gh(argv):
    """Run a gh command; return stdout, or exit 1 with gh's error."""
    try:
        proc = subprocess.run(["gh", *argv], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        fail(1, "gh CLI not found. Install gh and run 'gh auth login'.")
    if proc.returncode != 0:
        fail(1, "'gh {}' failed: {}".format(" ".join(argv), proc.stderr.strip()))
    return proc.stdout


def normalize_color(raw, context):
    color = str(raw).strip().lstrip("#").lower()
    if not HEX_COLOR.match(color):
        fail(
            2,
            f"{context}: color {raw!r} is not a 6-digit hex value (use e.g. \"d73a4a\", without '#')",
        )
    return color


def load_desired(path):
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except OSError as exc:
        fail(2, f"cannot read {path}: {exc}")
    except json.JSONDecodeError as exc:
        fail(2, f"{path} is not valid JSON: {exc}")
    if not isinstance(data, list):
        fail(2, f"{path} must be a JSON array of label objects")
    labels = []
    seen = set()
    for index, item in enumerate(data):
        context = f"{path}[{index}]"
        if not isinstance(item, dict) or not str(item.get("name", "")).strip():
            fail(2, f"{context} must be an object with a non-empty 'name'")
        name = str(item["name"]).strip()
        key = name.lower()
        if key in seen:
            fail(2, f"{context}: duplicate label name {name!r}")
        seen.add(key)
        labels.append(
            {
                "name": name,
                "color": normalize_color(item.get("color", ""), context),
                "description": str(item.get("description") or "").strip(),
            }
        )
    if not labels:
        fail(2, f"{path} contains no labels")
    return labels


# gh paginates label listings; a truncated listing would classify existing
# labels as "create" and make the apply fail halfway through.
LABEL_PAGE_LIMIT = 1000


def fetch_current(repo):
    stdout = run_gh(
        [
            "label",
            "list",
            "-R",
            repo,
            "--json",
            "name,color,description",
            "--limit",
            str(LABEL_PAGE_LIMIT),
        ]
    )
    try:
        entries = json.loads(stdout)
    except json.JSONDecodeError:
        fail(1, "could not parse 'gh label list' output as JSON")
    if isinstance(entries, list) and len(entries) >= LABEL_PAGE_LIMIT:
        fail(
            1,
            f"{repo} returned {len(entries)} labels, at or above the "
            f"{LABEL_PAGE_LIMIT} listing limit — the listing may be "
            "truncated, which would turn existing labels into creates. "
            "Raise LABEL_PAGE_LIMIT and re-run.",
        )
    return {
        str(entry["name"]).lower(): {
            "name": str(entry["name"]),
            "color": str(entry.get("color", "")).lstrip("#").lower(),
            "description": str(entry.get("description") or "").strip(),
        }
        for entry in entries
    }


def build_plan(desired, current):
    create, update, skip = [], [], []
    for label in desired:
        existing = current.get(label["name"].lower())
        if existing is None:
            create.append(label)
        elif existing["color"] != label["color"] or existing["description"] != label["description"]:
            update.append(label)
        else:
            skip.append(label["name"])
    desired_keys = {label["name"].lower() for label in desired}
    prune_candidates = [entry["name"] for key, entry in sorted(current.items()) if key not in desired_keys]
    return create, update, skip, prune_candidates


def apply_plan(repo, create, update, prune_candidates, do_prune):
    for label in create:
        print(f"create: {label['name']}", file=sys.stderr)
        run_gh(
            [
                "label",
                "create",
                label["name"],
                "-R",
                repo,
                "--color",
                label["color"],
                "--description",
                label["description"],
            ]
        )
    for label in update:
        print(f"update: {label['name']}", file=sys.stderr)
        run_gh(
            [
                "label",
                "edit",
                label["name"],
                "-R",
                repo,
                "--color",
                label["color"],
                "--description",
                label["description"],
            ]
        )
    pruned = []
    if do_prune:
        for name in prune_candidates:
            print(f"delete: {name}", file=sys.stderr)
            run_gh(["label", "delete", name, "-R", repo, "--yes"])
            pruned.append(name)
    return pruned


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Sync a GitHub repository's labels to a JSON taxonomy file. "
            "Dry-run by default: prints the create/update/skip/prune plan "
            "as JSON to stdout without changing anything; re-run with "
            "--apply to execute it."
        ),
        epilog=(
            "Exit codes: 0 plan printed or applied cleanly, 1 gh missing "
            "or failed, 2 bad arguments or invalid labels file."
        ),
    )
    parser.add_argument(
        "--file",
        required=True,
        help=('path to the labels JSON file: an array of {"name", "color", "description"} objects'),
    )
    parser.add_argument("--repo", required=True, help="target repository as OWNER/REPO")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="execute the plan (default: dry-run, print the plan only)",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="with --apply, delete repo labels absent from the file",
    )
    args = parser.parse_args()

    if not REPO_SLUG.match(args.repo):
        fail(2, f"--repo must be OWNER/REPO, got {args.repo!r}")
    if args.prune and not args.apply:
        fail(
            2,
            "--prune requires --apply; the dry-run plan already reports prune candidates",
        )

    desired = load_desired(args.file)
    current = fetch_current(args.repo)
    create, update, skip, prune_candidates = build_plan(desired, current)

    pruned = []
    if args.apply:
        pruned = apply_plan(args.repo, create, update, prune_candidates, args.prune)

    plan = {
        "repo": args.repo,
        "applied": args.apply,
        "create": create,
        "update": update,
        "skip": skip,
        "prune_candidates": prune_candidates,
        "pruned": pruned,
    }
    json.dump(plan, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
