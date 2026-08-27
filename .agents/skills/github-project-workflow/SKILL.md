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
then pass `--label`, `--milestone`, and attach it as a sub-issue of the tracking issue:
`gh api repos/hoshiori-dev/annotools/issues/1/sub_issues -F sub_issue_id=<issue id>` (the id, not the
number). Conventions: `.agents/knowledge/planning.md`.

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
PEP 440 `rcN`). `gh release create v<version> --generate-notes [--prerelease]` triggers
`release.yml`: verify → build → smoke → GHCR. Read back `gh api repos/hoshiori-dev/annotools/rulesets`
before promising a required check exists.

## Gotchas

- Third-party action tags: verify `gh api repos/<o>/<r>/git/ref/tags/<tag>` first — `setup-uv` has no
  `vN` tag; unresolved tags fail every job at "Set up job".
- gitleaks (pre-commit) flags `::error::` annotations as IPv6 and needs non-capturing groups in custom
  rules; print `ERROR:` in scripts.
- A skipped job reports success; `ci-gate` checks test jobs actually ran on PR/main/release.
- The default token cannot read org issue types, Actions policy, or write rulesets (403): report the
  manual step instead of retrying.
- `gh issue develop --base <branch>` stacks a branch on an unmerged one; rebase onto `main` after the
  base merges before opening the PR against `main`.
