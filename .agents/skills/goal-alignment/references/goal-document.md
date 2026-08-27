# Assembling the goal document

Load this when assembling the complete draft for user confirmation. It fixes
the document's shape so every goal document reads the same way to a future
agent; the content of every section still comes from the elicitation, never
from boilerplate.

## Skeleton

Order the document as follows. Section names below are canonical English;
render headings in the conversation language, keeping this order and meaning.
Add subject-specific sections where they earn their place (see the last
section), positioned after Requirements and before Trade-off decisions.

1. **Header** — what is being created (one line), document status
   ("confirmed by <user> on <absolute date>"), and the scenario and target
   users established during framing. The header is what lets a future agent
   decide in seconds whether this document governs its task.
2. **Overall goal** — one short paragraph: why this thing should exist and
   what success looks like. No feature lists; those belong in concrete goals.
3. **Concrete goals** — one entry per goal, using the entry format below.
4. **Requirements** — two lists, "Do" and "Don't", using the requirement
   format below.
5. **Trade-off decisions** — one record per resolved conflict, using the
   record format below. If nothing conflicted, state that explicitly rather
   than omitting the section — silence reads as "nobody checked".

## Entry formats

Goal entry — every field present on every entry:

```markdown
- **<Goal statement, one sentence>**
  - Verification: <how a future agent tells the goal is met — a quantified
    baseline when the goal is quantifiable, otherwise the observable or
    judgment-based check agreed with the user>
  - Tier: <hard constraint | optimization target | preference>
```

Requirement entry:

```markdown
- **<Do or avoid what, one sentence>** — <mandatory | best-effort | preference>
```

Trade-off record:

```markdown
- **Conflict:** <the two pulls, named plainly>
  **Decision:** <what was chosen>
  **Rationale:** <why, as the user accepted it>
```

## Writing for a zero-context reader

The document must stand alone; the conversation that produced it will not be
available.

- Never reference the dialogue — no "as discussed", "per your last message",
  or "we agreed earlier". State the conclusion itself.
- Define subject-specific terms at first use, or in the header when they
  pervade the document.
- Use absolute dates, never "today" or "next quarter".
- Record decisions, not deliberation: the trade-off section carries the
  rationale; everywhere else states outcomes.

## Subject-specific sections

Different subjects justify different additions — an experiment may add a
hypotheses section, a service may add service-level objectives, a library may
add compatibility commitments. These are examples, not a list to choose
from: add a section when the subject has goal-relevant structure the minimum
sections cannot hold, and give each added section the same treatment —
verifiable statements, explicit tiers or enforcement levels where they
apply. Never add plan-, task-, or architecture-shaped sections; if the user
pushes implementation detail into the document, park it as a candidate
requirement and ask which goal it serves.
