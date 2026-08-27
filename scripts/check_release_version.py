"""Fail unless the release tag matches the project version in pyproject.toml.

Usage: check_release_version.py v0.2.0-rc1
Tags are ``v<semver>``; ``-rc1`` style pre-release suffixes are compared against PEP 440 (``0.2.0rc1``).
"""

import sys
import tomllib
from pathlib import Path

from packaging.version import Version


def main(tag: str) -> int:
    """Compare ``tag`` with the version declared in pyproject.toml."""
    if not tag.startswith("v"):
        print(f"::error::Release tag {tag!r} must start with 'v'.")
        return 1
    project_version = tomllib.loads(Path("pyproject.toml").read_text())["project"]["version"]
    try:
        tag_version = Version(tag[1:])
    except ValueError:
        print(f"::error::Release tag {tag!r} is not a valid version (expected v<major>.<minor>.<patch>[-rcN]).")
        return 1
    if tag_version != Version(project_version):
        print(f"::error::Tag version {tag_version} does not match pyproject.toml version {project_version}.")
        return 1
    print(f"Tag {tag} matches pyproject.toml version {project_version}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
