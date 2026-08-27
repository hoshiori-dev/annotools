# Design-tree rounds

Load when running an interview round.

## Collections
- **Facts**: things the environment can prove (item counts, sizes, formats, available models, existing
  labels). Look them up; never ask.
- **Decisions**: choices only the user can make. Each has prerequisites (other decisions or facts).
- **Frontier**: every decision whose prerequisites are settled and that is still open.

## Round procedure
1. Recompute the frontier. Dispatch lookups for any fact a frontier question needs; do not block the
   rest of the round on them — only the dependent questions wait.
2. Ask the whole frontier in one message: numbered questions, each with one recommended answer in
   brackets and a one-line reason. A question whose answer depends on another open question in the
   same round belongs to the next round.
3. Wait for the user. Apply the answers; a conflict between answers becomes an explicit trade-off
   question in the next round instead of a silent choice.
4. Repeat until the frontier is empty, then present the complete spec draft for confirmation.

## Done when
No decision is left open and nothing was silently assumed: every default the user did not confirm is
listed under "assumptions" in the spec draft.

## Anti-patterns
- One question per message (slow; hides dependencies).
- Asking for facts the repo or the data can answer.
- Scaffolding files before the user confirms the draft.
