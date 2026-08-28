"""Tests for scripts/prepare_release_tag.py.

The script decides which tag a release-preparation run will create, so a mistake here either tags the
wrong version or lets a second tag be cut for a version that was already released.
"""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare_release_tag.py"


@pytest.fixture
def project(tmp_path: Path):
    """A throwaway project directory whose pyproject.toml version the test controls."""

    def make(version: str) -> Path:
        root = tmp_path / "project"
        root.mkdir(exist_ok=True)
        (root / "pyproject.toml").write_text(f'[project]\nname = "x"\nversion = "{version}"\n')
        return root

    return make


def run(cwd: Path, refs: str = "", *args: str) -> subprocess.CompletedProcess:
    """Run the script with ``refs`` on stdin, as `git ls-remote --tags` would provide them."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=refs,
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
        env={"PATH": "/usr/bin:/bin"},
    )


def ls_remote(*names: str) -> str:
    return "".join(f"0000000000000000000000000000000000000000\trefs/tags/{name}\n" for name in names)


@pytest.mark.parametrize(
    ("version", "expected"),
    [("0.1.0", "v0.1.0"), ("0.1.0rc1", "v0.1.0-rc1"), ("2.0.0a3", "v2.0.0-a3"), ("1.4.0b2", "v1.4.0-b2")],
)
def test_derives_the_canonical_tag(project, version: str, expected: str) -> None:
    """Derivation follows the documented form v<semver>[-rcN], not a bare concatenation."""
    proc = run(project(version))
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == expected


def test_explicit_tag_that_agrees_is_kept(project) -> None:
    proc = run(project("0.1.0rc1"), "", "--tag", "v0.1.0-rc1")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "v0.1.0-rc1"


def test_explicit_tag_spelling_is_preserved(project) -> None:
    """An explicit tag is used verbatim; the script does not rewrite what the operator asked for."""
    proc = run(project("0.1.0rc1"), "", "--tag", "v0.1.0rc1")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "v0.1.0rc1"


def test_explicit_tag_that_disagrees_fails(project) -> None:
    """This is the reason to pass a tag at all: it asserts what you believe you are releasing."""
    proc = run(project("0.1.0rc1"), "", "--tag", "v0.2.0")
    assert proc.returncode == 1
    assert "ERROR:" in proc.stderr
    assert not proc.stdout.strip()


def test_explicit_tag_without_v_prefix_fails(project) -> None:
    proc = run(project("0.1.0rc1"), "", "--tag", "0.1.0-rc1")
    assert proc.returncode == 1
    assert "ERROR:" in proc.stderr


def test_duplicate_is_detected_across_spellings(project) -> None:
    """The whole point: v0.1.0rc1 and v0.1.0-rc1 are the same release, spelled differently."""
    proc = run(project("0.1.0rc1"), ls_remote("v0.1.0rc1"))
    assert proc.returncode == 1
    assert "ERROR:" in proc.stderr
    assert "v0.1.0rc1" in proc.stderr


def test_unrelated_tags_do_not_block(project) -> None:
    proc = run(project("0.2.0"), ls_remote("v0.1.0", "v0.1.0-rc1", "not-a-version"))
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "v0.2.0"


def test_annotated_tag_refs_are_collapsed(project) -> None:
    """`git ls-remote --tags` lists an annotated tag twice, the second as refs/tags/<name>^{}."""
    refs = ls_remote("v0.1.0-rc1") + "1111111111111111111111111111111111111111\trefs/tags/v0.1.0-rc1^{}\n"
    proc = run(project("0.1.0rc1"), refs)
    assert proc.returncode == 1
    error = next(line for line in proc.stderr.splitlines() if line.startswith("ERROR:"))
    assert error.count("v0.1.0-rc1") == 1, "the same tag must be reported once, not twice"


def test_existing_tag_ok_accepts_the_tag_itself(project) -> None:
    """On the tag-push path the tag being prepared already exists; that is not a conflict."""
    proc = run(project("0.1.0rc1"), ls_remote("v0.1.0-rc1"), "--tag", "v0.1.0-rc1", "--existing-tag-ok")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "v0.1.0-rc1"


def test_existing_tag_ok_still_rejects_a_differently_spelled_twin(project) -> None:
    refs = ls_remote("v0.1.0-rc1", "v0.1.0rc1")
    proc = run(project("0.1.0rc1"), refs, "--tag", "v0.1.0-rc1", "--existing-tag-ok")
    assert proc.returncode == 1
    assert "v0.1.0rc1" in proc.stderr


def test_refuses_to_derive_a_form_the_convention_has_no_spelling_for(project) -> None:
    """post/dev/epoch versions have no v<semver>[-rcN] spelling and no valid semver image either."""
    proc = run(project("0.1.0.dev1"))
    assert proc.returncode == 1
    assert "ERROR:" in proc.stderr
    assert "--tag" in proc.stderr, "the error must say how to proceed"


def test_explicit_tag_is_allowed_for_such_a_version(project) -> None:
    """Refusing to *derive* one must not forbid releasing one deliberately."""
    proc = run(project("0.1.0.dev1"), "", "--tag", "v0.1.0.dev1")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "v0.1.0.dev1"
