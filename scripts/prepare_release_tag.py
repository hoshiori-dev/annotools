"""Resolve the tag a release-preparation run should create, and refuse a version already tagged.

Usage: git ls-remote --tags origin | prepare_release_tag.py [--tag v0.2.0-rc1] [--existing-tag-ok]

Without ``--tag`` the tag is derived from ``pyproject.toml`` in the canonical form ``v<semver>[-rcN]``.
With ``--tag`` the value is used verbatim and must agree with ``pyproject.toml``; that disagreement is
the reason to pass one — it asserts what the operator believes they are releasing.

Existing tags are compared as PEP 440 versions, not as strings: ``v0.1.0rc1`` and ``v0.1.0-rc1`` are the
same release spelled two ways, and only a version comparison catches the second one. ``--existing-tag-ok``
is for the tag-push path, where the tag being prepared is expected to exist already; a differently
spelled tag of the same version is still a conflict.

The resolved tag goes to stdout, alone, so a caller can capture it. Everything else goes to stderr.
"""

import argparse
import sys
import tomllib
from pathlib import Path

from packaging.version import InvalidVersion, Version


def canonical_tag(version: Version) -> str:
    """Spell ``version`` the way this project tags releases: ``v<semver>[-rcN]``.

    Raises:
        ValueError: If the version is an epoch, post, dev or local version. Those have no spelling in
            this convention and are not valid semver either, so `docker/metadata-action` could not tag
            an image for them. The caller is told to pass `--tag` rather than being given an invented
            form — and a local version would otherwise be dropped silently, since the parts this
            function keeps do not include it.
    """
    if version.epoch or version.is_postrelease or version.is_devrelease or version.local:
        raise ValueError(
            f"cannot derive a canonical tag for {version}: the v<semver>[-rcN] convention has no "
            "spelling for epoch, post, dev or local versions. Pass --tag explicitly if that is intended."
        )
    if version.pre is None:
        return f"v{version.base_version}"
    phase, number = version.pre
    return f"v{version.base_version}-{phase}{number}"


def tag_names(lines: list[str]) -> list[str]:
    """Tag names from `git ls-remote --tags` output, with each name appearing once.

    An annotated tag is listed twice, the second time as ``refs/tags/<name>^{}``; both collapse to the
    same name, and reporting a conflict twice would only be noise.
    """
    names: list[str] = []
    for line in lines:
        _, _, ref = line.strip().partition("refs/tags/")
        name = ref.removesuffix("^{}")
        if name and name not in names:
            names.append(name)
    return names


def conflicts(names: list[str], version: Version, keep: str | None) -> list[str]:
    """Existing tags that are the same release as ``version``, ignoring the tag named ``keep``."""
    found = []
    for name in names:
        if name == keep:
            continue
        try:
            existing = Version(name.removeprefix("v"))
        except InvalidVersion:
            continue  # Not a release tag; the repository may carry any other tag it likes.
        if existing == version:
            found.append(name)
    return found


def main(argv: list[str], refs: list[str]) -> int:
    """Resolve the tag, print it to stdout, and return 0 only when it may be created."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="Tag to use verbatim; must match pyproject.toml.")
    parser.add_argument(
        "--existing-tag-ok",
        action="store_true",
        help="The tag already exists and that is expected (the tag-push path).",
    )
    args = parser.parse_args(argv)

    project_version = Version(tomllib.loads(Path("pyproject.toml").read_text())["project"]["version"])

    if args.tag is None:
        try:
            tag = canonical_tag(project_version)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"Derived {tag} from pyproject.toml version {project_version}.", file=sys.stderr)
    else:
        tag = args.tag
        if not tag.startswith("v"):
            print(f"ERROR: Release tag {tag!r} must start with 'v'.", file=sys.stderr)
            return 1
        try:
            tag_version = Version(tag[1:])
        except InvalidVersion:
            print(f"ERROR: Release tag {tag!r} is not a valid version.", file=sys.stderr)
            return 1
        if tag_version != project_version:
            print(
                f"ERROR: Tag version {tag_version} does not match pyproject.toml version {project_version}.",
                file=sys.stderr,
            )
            return 1

    clashing = conflicts(tag_names(refs), project_version, keep=tag if args.existing_tag_ok else None)
    if clashing:
        print(
            f"ERROR: version {project_version} is already tagged as {', '.join(clashing)}. "
            "Bump the version, or delete that tag if it was never released.",
            file=sys.stderr,
        )
        return 1

    print(tag)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], sys.stdin.readlines()))
