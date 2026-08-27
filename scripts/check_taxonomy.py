#!/usr/bin/env python3
"""Check that every label referenced anywhere in the repository's harness
exists in the committed taxonomy.

Copy into the target repository at scripts/check_taxonomy.py and run it as
the `taxonomy / consistency` CI job. Sources checked against labels.json:

- .github/release.yml           category and exclude labels ('*' ignored)
- .github/ISSUE_TEMPLATE/*.yml  top-level `labels:` (config.yml skipped)
- .github/labeler.yml           top-level label keys

A referenced-but-undefined label is exactly the failure GitHub never
reports: forms and release.yml drop unknown labels silently.

Dependency exception: parsing workflow-adjacent YAML requires PyYAML,
which is not in the standard library. This is the repository's one
documented script dependency: install with `pip install pyyaml==6.0.2`
(the CI job does the same). --help works without it.

Usage:
    python3 scripts/check_taxonomy.py [--repo-root DIR] [--labels FILE]

Exit codes: 0 = every referenced label is defined, 1 = at least one
undefined reference (each printed with its source file), 2 = bad
arguments, unreadable inputs, or PyYAML missing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def fail(code: int, message: str) -> None:
    print(f"check_taxonomy: error: {message}", file=sys.stderr)
    sys.exit(code)


def import_yaml():
    """Import PyYAML after argument parsing so --help needs no dependency."""
    try:
        import yaml
    except ImportError:
        fail(
            2,
            "PyYAML is required — install with `pip install pyyaml==6.0.2` "
            "(the one documented dependency exception for this repository's "
            "scripts).",
        )
    return yaml


def load_defined(labels_path: Path) -> set:
    try:
        entries = json.loads(labels_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(2, f"cannot read {labels_path}: {exc}")
    if not isinstance(entries, list):
        fail(2, f"{labels_path} must be a JSON array of label objects")
    return {str(e.get("name", "")) for e in entries if isinstance(e, dict)}


def load_yaml_file(path: Path):
    yaml = import_yaml()
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        fail(2, f"cannot read {path}: {exc}")
    except yaml.YAMLError as exc:
        fail(2, f"cannot parse {path}: {exc}")


def as_dict(value):
    """A YAML key written with no value parses as None, not {}."""
    return value if isinstance(value, dict) else {}


def as_list(value):
    """A YAML key written with no value parses as None, not []."""
    return value if isinstance(value, list) else []


def collect_references(root: Path) -> list:
    """Return (label, source) pairs for every label reference found."""
    refs = []
    release = root / ".github" / "release.yml"
    if release.is_file():
        changelog = as_dict(as_dict(load_yaml_file(release)).get("changelog"))
        for label in as_list(as_dict(changelog.get("exclude")).get("labels")):
            refs.append((str(label), release))
        for entry in as_list(changelog.get("categories")):
            category = as_dict(entry)
            for label in as_list(category.get("labels")):
                refs.append((str(label), release))
            for label in as_list(as_dict(category.get("exclude")).get("labels")):
                refs.append((str(label), release))
    template_dir = root / ".github" / "ISSUE_TEMPLATE"
    if template_dir.is_dir():
        for form in sorted(template_dir.glob("*.yml")) + sorted(template_dir.glob("*.yaml")):
            if form.name in ("config.yml", "config.yaml"):
                continue
            labels = as_dict(load_yaml_file(form)).get("labels")
            if isinstance(labels, str):
                labels = [part.strip() for part in labels.split(",") if part.strip()]
            for label in as_list(labels):
                refs.append((str(label), form))
    labeler = root / ".github" / "labeler.yml"
    if labeler.is_file():
        for label in as_dict(load_yaml_file(labeler)):
            refs.append((str(label), labeler))
    return refs


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check that release.yml, issue forms, and labeler.yml reference "
            "only labels defined in the committed taxonomy. Exit codes: "
            "0 = consistent, 1 = undefined references (listed), 2 = bad "
            "arguments, unreadable inputs, or PyYAML missing."
        ),
        epilog="Example: python3 scripts/check_taxonomy.py",
    )
    parser.add_argument("--repo-root", default=".", help="repository root (default: .)")
    parser.add_argument(
        "--labels",
        default=".github/labels.json",
        help="taxonomy file, relative to --repo-root (default: .github/labels.json)",
    )
    args = parser.parse_args()

    root = Path(args.repo_root)
    if not root.is_dir():
        fail(2, f"--repo-root {root} is not a directory")
    labels_path = root / args.labels
    if not labels_path.is_file():
        fail(2, f"taxonomy file {labels_path} not found — pass --labels")

    defined = load_defined(labels_path)
    undefined = [(label, source) for label, source in collect_references(root) if label not in defined and label != "*"]
    if undefined:
        for label, source in undefined:
            print(
                f"undefined label {label!r} referenced by {source} — add it to "
                f"{labels_path} (and sync it to the repository) or fix the "
                "reference; GitHub drops unknown labels silently.",
                file=sys.stderr,
            )
        return 1
    print(f"taxonomy consistent: {len(defined)} labels defined, all references resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
