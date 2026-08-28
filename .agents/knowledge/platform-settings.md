# GitHub Platform Settings and CI Map

Load this when touching workflows, diagnosing a red check, or changing anything about the remote
repository (rulesets, merge methods, secrets, environments).

Repository: `hoshiori-dev/annotools` · owner: organization · visibility: public · enforcement tier:
enforced (rulesets available). Actions enabled (workflows run); org policy details are not readable with
the default token.

## CI job ↔ command map

| Job (workflow) | Command | Runs on |
|---|---|---|
| `lint` (CI) | `uv run ruff check .` + `scripts/check_taxonomy.py` + `scripts/check_readme_sync.py` + `scripts/check_public_docstrings.py` | every push, PR |
| `format` (CI) | `uv run ruff format --check .` | every push, PR |
| `typecheck` (CI) | `uv run ty check` | every push, PR |
| `docs` (CI) | `uv run scripts/gen_mcp_reference.py --check` (generated tool reference is current) then `uv run zensical build --clean --strict` (warnings fail the build) | every push, PR |
| `pr-title` (CI) | Conventional Commits title check | PR |
| `test-unit` (CI) | `uv run pytest -m "not container" --cov --cov-report=term --cov-report=xml` (3.12, 3.13); fails below `fail_under = 95` from `pyproject.toml`, enforced per leg; `coverage.xml` uploaded as `coverage-<py>` | main push, `v*` tag push, PR, release |
| `test-container` (CI) | docker build + `uv run pytest -m container` | main push, `v*` tag push, PR, release |
| `ci-gate` (CI) | aggregates all of the above; required check | same |
| `secret-scan` (Secret Scanning) | TruffleHog `--results=verified,unknown` | main push, PR |
| `deploy` (Documentation) | `zensical build --clean --strict` → Pages | main push |
| `check-version` → `verify` (CI) → `build` → `smoke` + `scan` (Release Tests) | see `release-tests.yml`; `scan` runs TruffleHog over the distributions and the image layers, gitleaks over the first-party files | called by Release Prepare and Release |
| Release Prepare: `resolve` → `tests` (Release Tests) → `draft-release` | see `release-prepare.yml`; creates the tag and a draft release only after the gate passes | `workflow_dispatch` with a `tag` input, or a pushed `v*` tag |
| Release: `tests` (Release Tests) → `publish-ghcr` + `publish-testpypi` → `publish-pypi` | see `release.yml`; `publish-pypi` runs only when `tests` reports the tag is not a PEP 440 pre-release | release published |
| Nightly: `changed` → `nightly` | see `nightly.yml`; container smoke test + image scan, then pushes the rolling `nightly` tag | 13:00 UTC (22:00 JST) daily, `workflow_dispatch` |

A commit on a PR branch produces two CI runs (push + pull_request); the push run shows the test jobs as
`skipped` by design, while the pull_request run executes them — read the pull_request run.

Rules: never weaken or delete a check to make it pass; a renamed job must be renamed in the ruleset in
the same change. Read failed logs with `gh run view <id> --log-failed`, not the full log.

## Reusable workflows and composite actions

- A called workflow (`workflow_call`) inherits the **caller's** event context. A call made from a
  tag-triggered workflow arrives as `push` on `refs/tags/*`, so any `if:` written against
  `github.event_name`/`github.ref` must account for the tag ref, or the job skips — and a skipped job
  reports success. `ci-gate` exists to catch exactly that.
- Artifacts uploaded inside a called workflow belong to the **caller's** run, so the caller's other jobs
  can download them. This is what lets `release.yml` publish the same wheel `release-tests.yml` tested.
- A composite action cannot hold a job graph — it is a step list inside one job, with no `uses:` of a
  workflow, no matrix, no fan-out. Share a multi-job chain as a reusable workflow and steps inside one
  job as a composite action. Nesting is limited to four levels
  (`release-prepare` → `release-tests` → `ci` is three).
- Caller side: a `uses:` job must grant every permission the called workflow's jobs declare
  (`ci.yml`'s `pr-title` needs `pull-requests: read`); a called workflow may not exceed the caller's grant.

## Verifying CI that needs docker

The devcontainer has no docker unless it was rebuilt, so image steps cannot run locally. Substitutes
that caught real problems: `actionlint` (install with the official download script) for workflow syntax;
replaying a scanner's rule file in Python against a real `uv build` output to predict findings before
CI runs it; checking a pinned scanner image tag exists with an anonymous GHCR token
(`curl "https://ghcr.io/token?scope=repository:<o>/<n>:pull&service=ghcr.io"`, then a manifest HEAD)
— note the tag conventions differ: `trufflesecurity/trufflehog:3.97.1` has no `v`, `gitleaks/gitleaks:v8.24.2` does.

## Remote settings

| Concern | Intended state | Owner | Verify |
|---|---|---|---|
| Merge methods | squash only; title = PR title, body = PR body; delete branch on merge; auto-merge allowed | repo admin | `gh api repos/hoshiori-dev/annotools` |
| Ruleset `main` | restrict deletions, block force pushes, require PR (0 approvals, squash), required checks `ci-gate` + `secret-scan` (not strict); bypass: repository admin | repo admin | `gh api repos/hoshiori-dev/annotools/rulesets` |
| Legacy branch protection | none | repo admin | branch protection UI |
| CODEOWNERS | requests review only; not enforced | repo admin | `gh api repos/hoshiori-dev/annotools/codeowners/errors` |
| Security | CodeQL default setup (org), Dependabot version updates via `.github/dependabot.yml`, private vulnerability reporting | repo admin | repository security settings |
| Secrets / variables | none required; publishing uses OIDC, never a token | repo admin | `gh variable list` |
| Environments | `pypi` and `testpypi`, created by the first run that references them, with no protection rules — which is the intent; the name is half the OIDC claim, so it selects the index. Configuring one by hand needs org-repo admin, which the working token does not have | created by the workflow | `gh api repos/hoshiori-dev/annotools/environments` |
| Trusted publishers | pypi.org and test.pypi.org both: owner `hoshiori-dev`, repository `annotools`, workflow `release.yml`, environment `pypi` / `testpypi` | PyPI account owner | the project's Publishing settings on each index |
| GHCR package | `ghcr.io/hoshiori-dev/annotools`, set public after the first push; tags `<version>` (every release), `<major>.<minor>` + `latest` (full releases), `nightly` (rolling, from main) | repo admin | package settings |

Status 2026-08-27: merge-method and ruleset changes returned 403 for the working token and are pending
manual application through the web UI (Settings → General → Pull Requests; Settings → Rules → Rulesets).
Until the ruleset is active, `ci-gate` and `secret-scan` are advisory.
