"""Fail unless the release tag matches the project version in pyproject.toml.

Usage: check_release_version.py v0.2.0-rc1
Tags are ``v<semver>``; ``-rc1`` style pre-release suffixes are compared against PEP 440 (``0.2.0rc1``).

On a match, when ``GITHUB_OUTPUT`` is set, writes ``prerelease=true|false`` from PEP 440. This is the
only place that decision is made: it marks the draft release and it decides whether the upload stops at
TestPyPI or continues to PyPI. A rejected tag writes nothing, so a failure can never route an upload.
"""

import os
import sys
import tomllib
from pathlib import Path

from packaging.version import Version


def main(tag: str) -> int:
    """Compare ``tag`` with the version declared in pyproject.toml."""
    if not tag.startswith("v"):
        print(f"ERROR: Release tag {tag!r} must start with 'v'.")
        return 1
    project_version = tomllib.loads(Path("pyproject.toml").read_text())["project"]["version"]
    try:
        tag_version = Version(tag[1:])
    except ValueError:
        print(f"ERROR: Release tag {tag!r} is not a valid version (expected v<major>.<minor>.<patch>[-rcN]).")
        return 1
    if tag_version != Version(project_version):
        print(f"ERROR: Tag version {tag_version} does not match pyproject.toml version {project_version}.")
        return 1
    print(f"Tag {tag} matches pyproject.toml version {project_version}.")
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        prerelease = str(tag_version.is_prerelease).lower()
        with Path(github_output).open("a", encoding="utf-8") as handle:
            handle.write(f"prerelease={prerelease}\n")
        print(f"prerelease={prerelease}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
