# Planning Objects on GitHub

Load this before creating or editing issues, labels, milestones, or the tracking issue.

## Source Of Truth

`.github/labels.json` for labels (synced with `just sync-labels [--apply]`); GitHub for milestones and
issues; the current cycle's tracking issue (named under "Current cycle" in `AGENTS.md`) and
`ARCHITECTURE.md` (Decisions) for the approved scope — plans are not committed.

## Structure

- Each development cycle has one tracking issue carrying the cycle goal, observable completion,
  carry-overs, and the sub-issue tree; the project vision and non-goals live in the first tracking
  issue (#1) and `ARCHITECTURE.md`. A closed cycle keeps its tracking issue as the record, closed
  with a final-status comment that links the carry-over issues filed in the next cycle.
- Milestones are phase buckets named `P<n> <theme>` (no due dates); a cycle owns one or more; every
  work item is a sub-issue of the cycle's tracking issue with a milestone. Close a milestone when it
  is drained.
- Issue types are the organization's native Task / Bug / Feature (set by the forms' `type:`; verify in
  the UI — the API is not readable with the default token).
- Labels: GitHub defaults kept as-is; `priority/high|medium|low`; `status/needs-triage` (applied by forms,
  removed once type and priority are set) and `status/blocked`; `area/mcp|skills|examples|harness|docs`
  matching CODEOWNERS paths and `release.yml` categories.
- No GitHub Projects. Day-to-day view is issue filters and the PR list.

## Creating issues non-interactively

`gh issue create` ignores forms. Mirror the Task form's `### <label>` headings — Content, Outcome,
Context and references, Solution direction and breakdown, Acceptance criteria, Out of scope, Cautions —
and pass labels and milestone explicitly. Draft user-facing text in the user's language for review, then
publish in English. Run the sensitivity check on the exact payload first.
