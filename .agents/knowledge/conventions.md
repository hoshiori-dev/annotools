# Python and Repository Conventions

Load this when writing or editing Python, tests, docstrings, lint/type configuration, pre-commit hooks,
or CI job commands.

## Source Of Truth

`pyproject.toml` (ruff, ty, pytest, coverage), `.pre-commit-config.yaml`, `justfile`, and
`.github/workflows/ci.yml` are the executable truth; this file records the reasoning and the gotchas.

## Code

- Google-style docstrings for public modules, classes, and functions and for anything non-obvious;
  comments explain why, not what. `tests/` and `scripts/` are exempt from docstring rules.
- ruff `select = E, F, I, UP, B, SIM, N, D, RUF`, line length 120; ruff also formats Python code blocks
  inside Markdown, so `docs/` examples must be formatted.
- ty is the type checker (`include = src, tests`); keep annotations complete on new code. No mypy.
- Library functions accept/return PIL images or bytes and raise `ValueError` for contract violations
  (odd polygon coordinate count, non-single-channel mask, coordinates outside 0–1).
- Defaults live in `annotools.config`; tools reference them instead of repeating literals.

## Tests

- pytest, classical style: real objects, generated fixtures (small synthetic images, no committed
  binaries), one behavior per test, parametrize families of cases with readable ids.
- FastMCP server tests use the in-memory transport: `async with Client(mcp) as client` — no subprocess.
  `pytest-asyncio` runs with `asyncio_mode = "auto"`.
- Tests that need docker carry `@pytest.mark.container` and are deselected by `just test`; run them with
  `just test-container` after `just docker-build`. Every documented raise gets a test.

## Toolchain

- uv manages environments and the lockfile; `uv sync --all-extras` for development. `just` is the task
  entrypoint (installed by the devcontainer's uv feature as `rust-just`; `uv tool install rust-just`
  otherwise). `just check` = what CI requires on a PR.
- pre-commit hook versions must match the dev dependency versions in `pyproject.toml` (ruff especially).
- gitleaks runs locally with `.gitleaks.toml` (PII rules: e-mails, public IPs). Custom rules must use
  non-capturing groups — with capturing groups gitleaks compares group 1 against the allowlist, which then
  never matches. Its IPv6 rule also matches GitHub annotations like `::error::…`: print `ERROR:` instead.
- Third-party GitHub Actions are pinned by tag (exception: `trufflesecurity/trufflehog@main`, the
  owner-provided secret-scan workflow); verify a tag exists before using it
  (`gh api repos/<owner>/<repo>/git/ref/tags/<tag>`) — `astral-sh/setup-uv` and
  `pypa/gh-action-pypi-publish` publish no major-version tag.

## APIs From Memory

- Verify library and SDK calls against `references/dependencies.md` / `references/agent-sdks.md`
  before writing them; add what you had to look up.

## Shell And Search Gotchas

- gitleaks' IPv6 rule (pre-commit) flags Python extended slices (`seq[start` + two colons + `step]`) as
  IPv6 literals — in code and in prose; pair values
  with `it = iter(values); zip(it, it)` instead of weakening the rule.
- Test scripts that ship inside `skills/` by loading them with `importlib.util.spec_from_file_location`
  (see `tests/test_skill_scripts.py`); a `sys.path` import cannot be resolved by `ty`.

- `rg` skips hidden directories: pass `--hidden` (and `--glob '!.git'`) or searches miss `.agents/` and
  `.github/`.
- The devcontainer shell is zsh: unquoted `$var` does not word-split — pipe file lists through `xargs`;
  in `sed 's#…#…#'` a replacement containing `#<n>` breaks the expression, so pick another delimiter.

## Validation

| Check | Command |
|---|---|
| Lint / format / types / taxonomy / README sync / unit tests | `just check` |
| Container tests | `just docker-build && just test-container` |
| Workflow YAML | `actionlint` |
