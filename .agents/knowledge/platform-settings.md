# GitHub Platform Settings and CI Map

Load this when touching workflows, diagnosing a red check, or changing anything about the remote
repository (rulesets, merge methods, secrets, environments).

Repository: `hoshiori-dev/annotools` · owner: organization · visibility: public · enforcement tier:
enforced (rulesets available). Actions enabled (workflows run); org policy details are not readable with
the default token.

## CI job ↔ command map

| Job (workflow) | Command | Runs on |
|---|---|---|
| `lint` (CI) | `uv run ruff check .` + `scripts/check_taxonomy.py` + `scripts/check_readme_sync.py` | every push, PR |
| `format` (CI) | `uv run ruff format --check .` | every push, PR |
| `typecheck` (CI) | `uv run ty check` | every push, PR |
| `docs` (CI) | `uv run zensical build --clean --strict` (warnings fail the build) | every push, PR |
| `pr-title` (CI) | Conventional Commits title check | PR |
| `test-unit` (CI) | `uv run pytest -m "not container" --cov --cov-report=term --cov-report=xml` (3.12, 3.13); fails below `fail_under = 95` from `pyproject.toml`, enforced per leg; `coverage.xml` uploaded as `coverage-<py>` | main push, PR, release |
| `test-container` (CI) | docker build + `uv run pytest -m container` | main push, PR, release |
| `ci-gate` (CI) | aggregates all of the above; required check | same |
| `secret-scan` (Secret Scanning) | TruffleHog `--results=verified,unknown` | main push, PR |
| `deploy` (Documentation) | `zensical build --clean --strict` → Pages | main push |
| Release: `check-version` → `verify` → `build` → `smoke` → `publish-ghcr` (→ `publish-pypi` disabled) | see `release.yml` | release published |

A commit on a PR branch produces two CI runs (push + pull_request); the push run shows the test jobs as
`skipped` by design, while the pull_request run executes them — read the pull_request run.

Rules: never weaken or delete a check to make it pass; a renamed job must be renamed in the ruleset in
the same change. Read failed logs with `gh run view <id> --log-failed`, not the full log.

## Remote settings

| Concern | Intended state | Owner | Verify |
|---|---|---|---|
| Merge methods | squash only; title = PR title, body = PR body; delete branch on merge; auto-merge allowed | repo admin | `gh api repos/hoshiori-dev/annotools` |
| Ruleset `main` | restrict deletions, block force pushes, require PR (0 approvals, squash), required checks `ci-gate` + `secret-scan` (not strict); bypass: repository admin | repo admin | `gh api repos/hoshiori-dev/annotools/rulesets` |
| Legacy branch protection | none | repo admin | branch protection UI |
| CODEOWNERS | requests review only; not enforced | repo admin | `gh api repos/hoshiori-dev/annotools/codeowners/errors` |
| Security | CodeQL default setup (org), Dependabot version updates via `.github/dependabot.yml`, private vulnerability reporting | repo admin | repository security settings |
| Secrets / variables | none required; `PYPI_PUBLISH_ENABLED` variable (unset) gates the PyPI job | repo admin | `gh variable list` |
| GHCR package | `ghcr.io/hoshiori-dev/annotools`, set public after the first push | repo admin | package settings |

Status 2026-08-27: merge-method and ruleset changes returned 403 for the working token and are pending
manual application through the web UI (Settings → General → Pull Requests; Settings → Rules → Rulesets).
Until the ruleset is active, `ci-gate` and `secret-scan` are advisory.
