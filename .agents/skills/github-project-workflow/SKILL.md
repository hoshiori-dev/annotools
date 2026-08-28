---
name: github-project-workflow
description: >-
  Runs annotools' GitHub lifecycle: taking or creating an issue, opening and finishing a pull request,
  publishing any issue/PR/comment/release text, diagnosing a red check, or cutting a release. Use when
  the user says "open an issue", "make a PR", "merge", "why is CI red", "release", or when work on an
  issue is about to start or finish. Not for changing the lifecycle policy itself (that needs user
  approval) and not for editing remote repository settings.
compatibility: Requires an authenticated `gh` CLI and Python 3 for scripts/run_log_digest.py.
---

# annotools GitHub Workflow

Repository `hoshiori-dev/annotools`, public, organization-owned, squash merge only. Every metadata change
(labels, milestone, assignee, state) is an explicit `gh` call. Language: publish in English; when the user
converses in another language, draft issue/PR text in that language for their review first, then publish
the English version.

## Take work

1. Read the issue; confirm it is open and its acceptance criteria are executable. If another identity is
   assigned, stop and ask whether duplicate work is intended.
2. `gh issue develop -c <n> --name <n>-<slug>` creates and checks out the branch. Push it and open a
   draft PR early with `Closes #<n>` — the draft PR is the claim and the work log.
3. Implement per the `spec-driven-feature` skill. Keep the PR description current.

## Create issues

`gh issue create` and `gh api` ignore issue forms. Mirror the Task form headings from
`.github/ISSUE_TEMPLATE/03-task.yml` as `### Content`, `### Outcome`, `### Context and references`,
`### Solution direction and breakdown`, `### Acceptance criteria`, `### Out of scope`, `### Cautions`,
then pass `--label`, `--milestone`, and attach it as a sub-issue of the current cycle's tracking issue
(number under "Current cycle" in `AGENTS.md`):
`gh api repos/hoshiori-dev/annotools/issues/<tracker>/sub_issues -F sub_issue_id=<issue id>` (the id,
not the number). Conventions: `.agents/knowledge/planning.md`.

## Publish gate

Every publishable write (issue, comment, PR body, release notes) runs this gate on the exact payload:

1. Write the final text to a scratch file. For a PR also review `git log main..HEAD` and
   `git diff main...HEAD` — a PR publishes its commits and diff, not only its description.
2. Scan for credentials, real personal data (emails other than `*@users.noreply.github.com`), internal
   hosts, unrelated files, and @-mentions of uninvolved people. `grep -iE '[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}|ghp_|sk-'`
   is the minimum; pre-commit's gitleaks already covers committed files.
3. Continue only on a verbatim `SAFE TO PUBLISH: YES` that you write after the scan. Any later edit
   re-runs the gate.
4. Publish non-interactively (`--body-file`), then read the result back (`gh pr view`, `gh issue view`).

## Finish a PR

1. `just check` green locally; push; wait for checks: `gh pr checks <n>` — poll with an `until` loop,
   never a fixed sleep.
2. Red check: `python3 .agents/skills/github-project-workflow/scripts/run_log_digest.py --repo hoshiori-dev/annotools --run-id <id>` (see
   [scripts/run_log_digest.py](scripts/run_log_digest.py)) or `gh run view <id> --log-failed`; never
   fetch the full log, never weaken or delete a check to make it pass. Job ↔ command map:
   `.agents/knowledge/platform-settings.md`.
3. Run the `retrospective-to-skill` skill; post the candidates as an issue comment.
4. Independent review: dispatch a clean-context subagent (strongest available model) with the PR number
   and the decisions already made; it must end with `VERDICT: APPROVE` or `VERDICT: REQUEST_CHANGES`.
   Fix findings, push, and re-request until APPROVE.
5. Complete the PR template checklist, `gh pr ready <n>`, then `gh pr merge <n> --squash --delete-branch`
   only when the user's standing authorization covers merging; otherwise stop and report.
6. Verify the linked issue closed (`gh issue view <n> --json state`). `git checkout main && git pull`.

## Releases

Tag `v<version>` must equal `pyproject.toml` (`scripts/check_release_version.py` checks; `-rcN` maps to
PEP 440 `rcN`). Never create the tag or the release by hand — the pipeline does both, and only after the
gate passes:

1. `gh workflow run release-prepare.yml -f tag=v<version>` from the commit to release. It validates the
   tag, runs `release-tests.yml` (CI → wheel and image build → smoke tests + credential/PII scan), then
   creates the tag and a draft release. `--prerelease` is set automatically from the version (PEP 440).
2. Review the generated notes on the draft.
3. Publish the draft **with user credentials** (`gh release edit v<version> --draft=false`, or the web
   UI). A draft published by `GITHUB_TOKEN` raises no event and nothing ships.
4. `release.yml` then re-runs the same gate and publishes: GHCR always, PyPI for a full release,
   TestPyPI for a pre-release. Watch it with `gh run watch`.

Read back `gh api repos/hoshiori-dev/annotools/rulesets` before promising a required check exists.

## Gotchas

- Third-party action tags: verify `gh api repos/<o>/<r>/git/ref/tags/<tag>` first — `setup-uv` has no
  `vN` tag; unresolved tags fail every job at "Set up job". Pinned container images used by workflows
  need the same check, and their conventions differ (`trufflehog:3.97.1` has no `v`, `gitleaks:v8.24.2` does).
- `gh issue create --milestone` matches the milestone's full title, not its `P<n>` prefix; read it back
  with `gh api repos/hoshiori-dev/annotools/milestones`.
- A tag pushed, or a draft release published, with `GITHUB_TOKEN` raises no event — no workflow reacts.
  Anything that must trigger a workflow is done by a person or a user token.
- gitleaks (pre-commit) flags `::error::` annotations as IPv6 and needs non-capturing groups in custom
  rules; print `ERROR:` in scripts.
- A skipped job reports success; `ci-gate` checks test jobs actually ran on PR/main/release.
- The default token cannot read org issue types, Actions policy, or write rulesets (403): report the
  manual step instead of retrying.
- `gh issue develop --base <branch>` stacks a branch on an unmerged one; rebase onto `main` after the
  base merges before opening the PR against `main`.
