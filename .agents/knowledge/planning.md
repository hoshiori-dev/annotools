# Planning Objects on GitHub

Load this before creating or editing issues, labels, milestones, or the tracking issue.

## Source Of Truth

`.github/labels.json` for labels (synced with `just sync-labels [--apply]`); GitHub for milestones and
issues; tracking issue #1 and `ARCHITECTURE.md` (Decisions) for the approved scope — plans are not committed.

## Structure

- Tracking issue #1 carries vision, non-goals, acceptance, and the sub-issue tree. Milestones P0–P6 are
  the phase buckets (no due dates); every work item is a sub-issue of #1 with a milestone.
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
