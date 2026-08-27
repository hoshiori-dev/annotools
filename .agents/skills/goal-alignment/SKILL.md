---
name: goal-alignment
description: >
  Goal alignment — relentlessly interrogates the user about what something
  should achieve, negotiating every open point to consensus, then records the
  outcome in a single source-of-truth goal document a future agent can work
  from alone. Use when defining what a thing must achieve before building
  it — "what are we actually trying to do", "align on the goals", "write a
  goal / north-star / charter document"; when starting any new software,
  package, system, experiment, skill, or service whose goals are not yet
  written down; when success criteria, constraints, or non-goals are fuzzy or
  disputed; or when stated goals conflict and the trade-off needs a recorded
  resolution. Not for implementation planning, task breakdown, or
  architecture design — the skill ends where the goal document is confirmed.
---

# Goal Alignment

A discipline for converging with the user on what something should achieve —
software, a package, a system, an experiment, a skill, a service, anything
being created — and recording the result as a goal document that is the
single source of truth. The reader of that document is a future agent with
zero context: it must be able to pick up the work knowing only what the
document says. Goals only — this skill never produces implementation plans,
task breakdowns, or architecture, because mixing "what to build" into "how to
build it" is exactly the failure the document exists to prevent.

## The consensus gate

Until the user confirms the complete draft presented in conversation, write
no files and take no other actions. Questions, suggestions, and every interim
draft live in the dialogue. A document written before consensus fabricates
the very fact it claims to record — that the user and agent agreed.

## The elicitation loop

1. **Frame the subject.** Establish what is being created, for whom, and in
   what scenario. Every suggested answer you give later is reasoned from
   these three facts, so pin them down first.
2. **Interrogate relentlessly.** Ask specific questions in rounds, grouped by
   theme. Whenever an answer can be inferred from what you already know —
   the frame, the draft so far, domain knowledge — attach your suggested
   answer to the question, because a question without a proposal pushes the
   whole burden of thought onto the user. When the answer is a fact only the
   user can know (an unstated goal, a budget, a deadline), ask directly
   instead — a fabricated suggestion only anchors the user to a guess.
   Everything is open to challenge: the user's stated requirements, your own
   earlier suggestions, and anything already in the draft may all be
   re-questioned against the scenario, the goals, and the target users. The
   user always decides. When two stated goals pull against each other,
   surface the tension as an explicit trade-off question with a proposed
   resolution rather than silently picking a side.
   Done when: no open items remain and every inferable question carried a
   suggested answer.
3. **Assemble and present the complete draft.** Read
   [references/goal-document.md](references/goal-document.md) when assembling
   the complete draft for user confirmation. Present the full draft in the
   conversation, not as a file.
4. **Write only after confirmation.** Once the user confirms the draft as
   presented, write the document (placement rules below) and hand the
   location back to the user.
   Done when: the user has confirmed the complete draft, the document exists
   at the correct location, and the user has been told where it is.

## What the document must contain

Sections beyond these are expected — different kinds of subjects need
different sections — but every goal document carries at least:

- **Overall goal** — a vision- or mission-level statement of why this thing
  should exist and what the world looks like when it succeeds.
- **Concrete goals** — itemized. Each entry states the goal, how it will be
  verified, and its tier (hard constraint / optimization target /
  preference). Quantified and unquantified verification have equal standing —
  both are legitimate — but when a goal can be quantified, prefer a
  quantified baseline, because it removes argument about whether the goal was
  met.
- **Requirements** — things to do and things not to do, each marked
  mandatory / best-effort / preference.
- **Trade-off decisions** — wherever goals or requirements conflicted, the
  conflict, the decision, and its rationale, so a future agent does not
  reopen a settled question by accident.

## Tier semantics

Tiers exist because they set how much freedom later design and execution
have to depart from the letter of the document:

- **Hard constraint** — no deviation without coming back to the user.
- **Optimization target** — maximize it; trade-offs against other goals are
  allowed when recorded.
- **Preference** — the default choice; later agents may propose alternatives.

Requirement enforcement levels mirror the same ladder: **mandatory** binds
like a hard constraint, **best-effort** like an optimization target, and
**preference** marks a default that may be challenged. Classify every goal
and requirement during elicitation — asking "is this a hard constraint or a
preference?" is itself one of the questions that exposes what the user
actually wants.

## Where the document goes

Default: create it as a temporary file in the session's scratchpad or
temporary directory and hand the user its absolute path, so the document is
reachable without touching the user's project. Use the harness-provided
scratchpad directory when one is announced; otherwise fall back to the
platform's temporary directory — `$TMPDIR` (or `/tmp` when unset) on Linux
and macOS, `%TEMP%` (typically `C:\Users\<name>\AppData\Local\Temp`) on
Windows. Depart from the default when:

- the goal work is one part of a larger deliverable (a plan, a proposal, a
  design document) — embed the goal content as a section of that host
  document, same structure, same consensus gate;
- the environment cannot show the user a temporary file's content — pick a
  location the user can actually read;
- the user or the surrounding context (a repository's documentation
  conventions, an explicit instruction) directs another location.

## Language

Write the goal document in the language of the conversation: the user must
be able to review the single source of truth without translation, and future
agents serving the same user will meet the same language.
