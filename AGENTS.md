# annotools

MCP server (FastMCP) plus Python library that let agents view and annotate multimodal data — images,
video, audio — within an MLLM token budget: downscale, crop-zoom, grid guide lines, and BBox / keypoint /
polygon / segmentation overlays. Publishable skills under `skills/` carry the SQLite-based annotation
methodology; `examples/` show Claude Agent SDK and Codex SDK pipelines. See `ARCHITECTURE.md` for layers.

## Project Map

```text
src/annotools/        <- library layer (image/video/audio/geometry/color/io) + MCP wrappers (tools/, server.py)
tests/                <- pytest; `container` marker needs docker
docs/                 <- zensical site; docs/spec/ (planned, P1) one spec per MCP tool; docs/plan/ the approved plan
skills/               <- (planned, P4) publishable skills (npx skills add hoshiori-dev/annotools); English
examples/             <- (planned, P5/P6) independent example projects; each has its own CONTEXT.md
.agents/knowledge/    <- agent knowledge base (this file routes into it)
.agents/skills/       <- development skills (Claude Code sees them via .claude/skills symlink)
.github/              <- workflows, issue forms, labels.json, release.yml, CODEOWNERS
scripts/              <- repo maintenance scripts (labels, taxonomy, release checks)
```

## Core Conventions

- Language: code, comments, docs, commits, issues, PRs in English. Talk to the user in the user's
  language; draft user-facing plans, issues, and PR text in that language for review, publish in English.
- `README.md` and `README.zh.md` are mirrors: change both in the same PR (`just readme-check`).
- Issue first, spec second, tests third: no feature work without an open issue; MCP tools and library
  contracts get a spec in `docs/spec/` (goal, parameters, return, acceptance criteria) mirrored in the
  issue; write the failing test before the implementation.
- Coordinates are normalized 0.0–1.0 relative to the uncropped source; colors are names or `#RRGGBB`.
- The library layer never imports `fastmcp`; MCP wrappers only validate parameters and encode results.
- Never store binary data in an annotation database — store file pointers (fsspec URL or local path).
- Changing anything under `examples/<project>/` requires reading that project's `CONTEXT.md` first;
  example projects do not use AGENTS.md.
- Python: Google-style docstrings for public contracts, ruff + ty, pytest with real objects over mocks.
  Details in `.agents/knowledge/conventions.md`.

## When To Read What

| Situation | Read |
|---|---|
| Writing or editing Python, tests, docstrings, lint config | `.agents/knowledge/conventions.md` |
| Writing a spec for an MCP tool or library feature | `.agents/knowledge/spec-format.md` |
| Choosing preview sizes, tiles, or token budgets for any model | `.agents/knowledge/mllm-token-budget.md` |
| Touching `examples/` | `.agents/knowledge/examples-context.md`, then the project's `CONTEXT.md` |
| Creating or editing issues, labels, milestones, tracking issues | `.agents/knowledge/planning.md` |
| Touching workflows, diagnosing a red check, remote settings | `.agents/knowledge/platform-settings.md` |
| Full design: modules, file structure, MCP interfaces, decisions | `docs/plan/2026-08-annotools-plan.zh.md` (Chinese, approved) |
| Issue → branch → draft PR → review → merge, publishing to GitHub | `.agents/skills/github-project-workflow/` |
| Implementing a feature end to end (issue, spec, tests, code) | `.agents/skills/spec-driven-feature/` |
| Before opening a PR: lessons learned, skill candidates | `.agents/skills/retrospective-to-skill/` |
| README changes | `.agents/skills/readme-bilingual-sync/` |

## Development Environment

- Devcontainer (`.devcontainer/`) with uv, `just`, docker-in-docker. `uv sync --all-extras` installs everything;
  `just` lists recipes. Without a rebuilt container there is no docker — image builds are verified by CI.
- The `annotools` MCP server is registered for Claude Code (`.mcp.json`), Codex (`.codex/config.toml`) and
  OpenCode (`opencode.json`) as `uv run annotools` (stdio). `just mcp-http` serves HTTP for debugging.
- Secrets never enter the repo: pre-commit runs gitleaks (PII rules), CI runs TruffleHog.

## Validation

| Check | Command |
|---|---|
| Everything CI requires on a PR (lint, format, types, taxonomy, README sync, unit tests) | `just check` |
| Container tests (needs docker; build first with `just docker-build`) | `just test-container` |
| Workflow YAML | `actionlint` (install via the official download script) |
| Docs build | `just docs` |

## Workflow

- Branch per issue (`gh issue develop -c <n>`), draft PR early with `Closes #n`, squash merge; the PR title is
  the commit message and must follow Conventional Commits (`pr-title` check).
- Before every PR: run the retrospective skill and list skill candidates in the issue thread.
- Publishing (issues, PRs, comments, releases) needs a sensitivity self-check on the exact payload;
  remote settings changes need explicit user approval.
- Releases: tag `v<version>` matching `pyproject.toml`; a `-rcN` pre-release publishes only to GHCR
  `<version>`; a full release also updates `<major>.<minor>` and `latest`. PyPI is a disabled placeholder.

## Keep In Sync

| When this changes | Update |
|---|---|
| A CI job is renamed or added | `.agents/knowledge/platform-settings.md` job map and the `main` ruleset required checks |
| A label, issue form, `release.yml`, or dependabot label | `.github/labels.json` — `just check-taxonomy` fails otherwise |
| An MCP tool's parameters or return | its `docs/spec/` file, tests, and README tool table (both languages) |
| A new knowledge file or development skill | this file's When To Read What table |
| Python tool versions in `pyproject.toml` dev group | matching `rev` in `.pre-commit-config.yaml` |
