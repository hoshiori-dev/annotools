---
name: retrospective-to-skill
description: >-
  Extracts the reusable lessons from a finished piece of work and decides which deserve to become a
  skill, a knowledge-file entry, or nothing. Use when a pull request is about to be marked ready, when the user
  asks "what did we learn", "should this be a skill", or after a debugging session with a non-obvious
  root cause. Not for writing the skill itself (use great-skill-writer or the project skill rules).
---

# Retrospective to Skill

## Workflow

1. **Collect candidates** from the branch: `git log main..HEAD --format=%B`, the issue thread, and the
   session — every moment where a fact had to be looked up, a tool behaved unexpectedly, a check failed
   for a non-obvious reason, or a decision was made that future agents must not re-derive.
   Done when: each candidate is one sentence stating the fact plus why it matters.
2. **Classify** each candidate with one default:
   - *Procedure* that is repeated, ordered, fragile, or branchy → **skill** (`.agents/skills/` for
     development, `skills/` if external users need it).
   - *Stable fact or gotcha* agents need when a condition fires → **knowledge file** entry
     (`.agents/knowledge/<topic>.md`), and a When-To-Read pointer in `AGENTS.md` if the file is new.
   - *Rule for every task* → one line in `AGENTS.md` Core Conventions.
   - *External fact looked up* (vendor rule, dependency API, SDK signature) → dated entry in
     `.agents/knowledge/references/`.
   - *Already recorded* or *one-off* → drop; say so.
3. **Post** the list as a comment on the issue (through the publish gate), formatted as
   `<n>. **<lesson>** → <destination> (#<issue if follow-up>)`; open a follow-up issue for any skill that
   will not be written in this PR.
4. **Apply** the knowledge-file and AGENTS.md entries in the same PR when they are short; larger skill
   work goes to the follow-up issue.

## Gotchas

- A lesson that only restates a tool's documentation is not a candidate unless the documentation was
  wrong or hard to find — record where the truth was.
- Do not write a skill for something that happened once; wait for the second occurrence or an explicit
  user request.
- `AGENTS.md` stays near 100 lines: prefer a knowledge-file entry over a new convention line.
