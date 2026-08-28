# annotools

MCP server (FastMCP) plus Python library that let agents view and annotate multimodal data — images,
video, audio — within an MLLM token budget: downscale, crop-zoom, grid guide lines, and BBox / keypoint /
polygon / segmentation overlays. Publishable skills under `skills/` carry the SQLite-based annotation
methodology; `examples/` show Claude Agent SDK and Codex SDK pipelines. See `ARCHITECTURE.md` for layers.

## Project Map

```text
src/annotools/        <- library layer (image/video/audio/geometry/color/io/config); mcp/ = FastMCP app, tool wrappers, CLI
tests/                <- pytest; `container` marker needs docker
docs/                 <- zensical site only (user-facing pages); specs are not here
skills/               <- publishable skills (npx skills add hoshiori-dev/annotools); English
examples/             <- independent example projects; each has its own CONTEXT.md
.agents/knowledge/    <- agent knowledge base (this file routes into it); spec/ one spec per MCP tool; references/ dated external facts
.agents/skills/       <- development skills (Claude Code sees them via .claude/skills symlink)
.github/              <- workflows, issue forms, labels.json, release.yml, CODEOWNERS
scripts/              <- repo maintenance scripts (labels, taxonomy, release checks)
```

## Core Conventions

- Language: code, comments, docs, commits, issues, PRs in English. Talk to the user in the user's
  language; draft user-facing plans, issues, and PR text in that language for review, publish in English.
- `README.md` and `README.zh.md` are mirrors: change both in the same PR (`just readme-check`).
- Issue first, spec second, tests third: no feature work without an open issue; MCP tools and library
  contracts get a spec in `.agents/knowledge/spec/` (goal, parameters, return, acceptance criteria) mirrored in the
  issue; write the failing test before the implementation.
- Coordinates are normalized 0.0–1.0 relative to the uncropped source; colors are names or `#RRGGBB`.
- The library layer never imports `fastmcp`; MCP wrappers only validate parameters and encode results.
- Never store binary data in an annotation database — store file pointers (fsspec URL or local path).
- Changing anything under `examples/<project>/` requires reading that project's `CONTEXT.md` first;
  example projects do not use AGENTS.md.
- Planning documents and design drafts are never committed; durable decisions go to `ARCHITECTURE.md` (Decisions) and
  `.agents/knowledge/`, scope to the tracking issue.
- Python: Google-style docstrings for public contracts, ruff + ty, pytest with real objects over mocks.
  Details in `.agents/knowledge/conventions.md`.

## When To Read What

| Situation | Read |
|---|---|
| Writing or editing Python, tests, docstrings, lint config | `.agents/knowledge/conventions.md` |
| Writing a spec for an MCP tool or library feature | `.agents/knowledge/spec-format.md` |
| Choosing preview sizes, tiles, or token budgets for any model | `.agents/knowledge/mllm-token-budget.md` |
| Any per-model fact: token cost, coordinate convention, cache minimum | `.agents/knowledge/references/mllm-models.md` |
| Using or upgrading FastMCP, pydantic-settings, PyAV, fsspec, Pillow | `.agents/knowledge/references/dependencies.md` |
| Writing Claude Agent SDK or Codex SDK pipeline code (examples, skills) | `.agents/knowledge/references/agent-sdks.md` |
| Touching `examples/` | `.agents/knowledge/examples-context.md`, then the project's `CONTEXT.md` |
| Creating or editing issues, labels, milestones, tracking issues | `.agents/knowledge/planning.md` |
| Touching workflows, diagnosing a red check, remote settings | `.agents/knowledge/platform-settings.md` |
| Module layout, data flow, recorded decisions | `ARCHITECTURE.md`; tool contracts in `.agents/knowledge/spec/` |
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
| Everything CI requires on a PR (lint, format, types, taxonomy, README sync, unit tests with the 95 % coverage gate, strict docs build) | `just check` |
| Container tests (needs docker; build first with `just docker-build`) | `just test-container` |
| Workflow YAML | `actionlint` (install via the official download script) |
| Docs build (strict, as CI) | `just docs-check` |

## Workflow

- Current cycle: tracking issue #77, milestone P8 (library identity). Every work item is one of its
  sub-issues; planning rules in `.agents/knowledge/planning.md`.
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
| A cycle opens or closes | the "Current cycle" line in this file (Workflow), the tracking issue's final-status comment |
| A CI job is renamed or added | `.agents/knowledge/platform-settings.md` job map and the `main` ruleset required checks |
| A label, issue form, `release.yml`, or dependabot label | `.github/labels.json` — `just check-taxonomy` fails otherwise |
| An MCP tool's parameters or return | its `.agents/knowledge/spec/` file, tests, and README tool table (both languages) |
| A new knowledge file or development skill | this file's When To Read What table |
| A vendor fact or dependency version | `.agents/knowledge/references/*.md` (date it) and the skill copy derived from it |
| Python tool versions in `pyproject.toml` dev group | matching `rev` in `.pre-commit-config.yaml` |
