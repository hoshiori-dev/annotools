# Working Inside Example Projects

Load this before creating, running, or modifying anything under `examples/`.

## Source Of Truth

Each example project's own `CONTEXT.md`; this file only states the repository-level rule.

## Rules

- Every `examples/<project>/` is an independent project with its own `CONTEXT.md` (not AGENTS.md — the
  root AGENTS.md governs this repository, `CONTEXT.md` governs the example). Read it first, follow it
  over root conventions where they differ, and keep it updated with the example.
- Example projects are complete on their own: `CONTEXT.md`, `spec/`, `config/`, `template/`, `skills/`,
  `scripts/`, `src/`, `workspaces/<task>/{data/raw,data/interim,data/dataset.db,output/}`, `justfile`.
- `data/raw/` is read-only for pipelines and agents; only the download script or a human places files
  there. Databases store file pointers, never binary blobs.
- Execution agents built in `src/` may only access their workspace directory; the tool allowlist in the
  SDK configuration enforces it.
- Each example README records the real usage of one full run (tokens, cost, wall time) and the model used.
- Examples are excluded from the root ruff/ty configuration; they carry their own checks.

## Environment notes

- Each example is its own uv project. The devcontainer exports `UV_PROJECT_ENVIRONMENT=/opt/uv/venv`
  globally; every example justfile pins `UV_PROJECT_ENVIRONMENT=.venv`, and `uv` run by hand inside an
  example needs the same override or it rewrites the root environment.
- Live runs need provider credentials (`ANTHROPIC_API_KEY`, or a Codex login) and network access to
  `images.cocodataset.org`; neither exists in the devcontainer, so usage records are filled from runs
  elsewhere.
- Examples pin copies of the skills they follow under `skills/` (`PINNED.txt`, `just sync-skills`).
