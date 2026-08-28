"""Tests for scripts/check_release_version.py.

The script gates every release: it decides whether a tag may be cut at all, and it is the single place
that decides whether a version is a pre-release, which routes the upload to TestPyPI or PyPI.
"""

import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "check_release_version.py"
PROJECT_VERSION = tomllib.loads((REPO / "pyproject.toml").read_text())["project"]["version"]


def run(tag: str, output_file: Path | None = None) -> tuple[subprocess.CompletedProcess, str]:
    """Run the script on ``tag``; return the process and the contents written to ``GITHUB_OUTPUT``."""
    env = {"PATH": "/usr/bin:/bin"}
    if output_file is not None:
        env["GITHUB_OUTPUT"] = str(output_file)
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), tag], capture_output=True, text=True, check=False, cwd=REPO, env=env
    )
    written = output_file.read_text() if output_file is not None and output_file.exists() else ""
    return proc, written


def test_matching_tag_passes(tmp_path: Path) -> None:
    proc, _ = run(f"v{PROJECT_VERSION}", tmp_path / "out")
    assert proc.returncode == 0, proc.stdout
    assert PROJECT_VERSION in proc.stdout


def test_emits_prerelease_flag_for_the_project_version(tmp_path: Path) -> None:
    """The flag routes the upload, so it must be emitted for whatever version the project is on."""
    out = tmp_path / "out"
    proc, written = run(f"v{PROJECT_VERSION}", out)
    assert proc.returncode == 0, proc.stdout
    from packaging.version import Version

    expected = str(Version(PROJECT_VERSION).is_prerelease).lower()
    assert f"prerelease={expected}" in written


@pytest.mark.parametrize(
    ("tag", "expected"),
    [("v1.2.3", "false"), ("v1.2.3-rc1", "true"), ("v1.2.3a1", "true"), ("v1.2.3.dev1", "true")],
)
def test_prerelease_flag_follows_pep440(tmp_path: Path, tag: str, expected: str, monkeypatch) -> None:
    """rc/alpha/beta/dev are pre-releases; a final version is not. Punctuation does not decide."""
    project = tmp_path / "project"
    (project / "scripts").mkdir(parents=True)
    (project / "pyproject.toml").write_text(f'[project]\nname = "x"\nversion = "{tag[1:]}"\n')
    out = tmp_path / "out"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), tag],
        capture_output=True,
        text=True,
        check=False,
        cwd=project,
        env={"PATH": "/usr/bin:/bin", "GITHUB_OUTPUT": str(out)},
    )
    assert proc.returncode == 0, proc.stdout
    assert f"prerelease={expected}" in out.read_text()


def test_mismatched_tag_fails(tmp_path: Path) -> None:
    proc, written = run("v99.99.99", tmp_path / "out")
    assert proc.returncode == 1
    assert proc.stdout.startswith("ERROR:")
    assert "prerelease=" not in written, "a rejected tag must not route an upload"


def test_tag_without_v_prefix_fails(tmp_path: Path) -> None:
    proc, written = run(PROJECT_VERSION, tmp_path / "out")
    assert proc.returncode == 1
    assert proc.stdout.startswith("ERROR:")
    assert "prerelease=" not in written


def test_unparseable_tag_fails(tmp_path: Path) -> None:
    proc, written = run("vnot-a-version", tmp_path / "out")
    assert proc.returncode == 1
    assert proc.stdout.startswith("ERROR:")
    assert "prerelease=" not in written


def test_runs_without_github_output(tmp_path: Path) -> None:
    """Outside Actions the script still works — it is run by hand when preparing a release."""
    proc, _ = run(f"v{PROJECT_VERSION}")
    assert proc.returncode == 0, proc.stdout
