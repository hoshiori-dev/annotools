# Contributing to annotools

## Setup and checks

Open the devcontainer or run `uv sync --all-extras`. Run `just check` before pushing — CI runs the same
commands (`.agents/knowledge/platform-settings.md` maps jobs to commands).

## Where things go

Bugs, features, and tasks → the issue forms. Vulnerabilities → private vulnerability reporting (see
`SECURITY.md`), never public issues.

## Working on a change

1. Open or pick an issue first; feature work starts with a spec in `.agents/knowledge/spec/` and a failing test.
2. Branch from `main` (`gh issue develop -c <number>` creates `<number>-<slug>`) and open a draft PR early
   with `Closes #<number>`.
3. Under squash merge the PR title becomes the commit message and must follow Conventional Commits
   (`feat:`, `fix:`, `docs:`, `ci:`, `build:`, `chore:`, …).
4. Keep `README.md` and `README.zh.md` in sync; write code, comments, docs, and PR text in English.
5. Mark the PR ready when the template checklist is complete and checks are green. Reviews are welcome
   but not required; the `ci-gate` and `secret-scan` checks are (enforced once the `main` ruleset is
   active — see `.agents/knowledge/platform-settings.md`).

## Merging and releases

Squash merge only. Releases are staged: the Release Prepare workflow takes a tag matching
`pyproject.toml`, runs the tests and scans the artifacts, and only then creates the tag and a draft
release. Publishing that draft repeats the gate and then publishes the container image to GHCR and the
wheel to PyPI — or to TestPyPI for a pre-release, which is a rehearsal channel rather than an install
path. A `nightly` image is built from main daily.
