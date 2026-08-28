# Interview the project into a spec

A labelling brief is never complete. "Box the cats" leaves open whether a tail counts, what happens
to a cat behind a chair, how small is too small, and which of three cats in a pile is one label or
three. Those questions get answered either in an interview or, silently and inconsistently, by the
model — twice, differently, on items 40 and 900.

The interview closes them before any code exists, and writes the answers to `spec/task.md`, which
every prompt, tool, and export then cites.

## The shape of the interview

It is a design tree rather than a questionnaire. Every settled decision unlocks the questions that
depend on it, so the agent asks the whole frontier of unblocked questions in one numbered round,
each with a recommended answer, waits, recomputes the frontier, and repeats. One question per
message hides the dependencies and takes an hour instead of ten minutes.

The split that keeps this honest: **facts** are the agent's job (how many files, what sizes, which
models are available, whether labels already exist — look at 20 items with `preview_image_grid`
before proposing a class list); **decisions** are the user's. Asking a user for a fact the data can
answer wastes a round; deciding something on the user's behalf and not saying so produces a spec
that nobody agreed to. Anything the user did not confirm is listed as an assumption in the draft.

Round 1 settles the trunk — task family, where the data lives, output format, model and provider,
budget per item, quality bar, label language, and any existing examples. Round 2 asks only the
branch that the chosen task family opened: caption length budgets and focus order, or a class list
with include/exclude rules and confusable pairs, or a keypoint skeleton, or a mask type, or video
sampling rates. Model choice belongs in round 1 because it decides the preview size and the
coordinate convention, which the [token budget](token-budget.md) step then locks in.

## Scaffolding, and not before

Nothing is generated until the user has accepted a trial: one to three items labelled by hand with
the agreed prompt, shown back with the image. A spec that looks right in prose and wrong on the
first real image is cheap to fix at that point and expensive later, because it has propagated into
every prompt.

After acceptance the skill scaffolds a fixed layout — `spec/`, `config/`, `src/`, `scripts/`,
`skills/`, a `template/workspace/` copied per dataset, and `workspaces/<task>/` holding
`data/raw/` (read-only), `data/interim/`, `data/dataset.db`, and `output/` — plus a `CONTEXT.md`
that is the agent entry point for that project and a `justfile` with `init`, `trial`, `run`,
`export`, `check`.

Three invariants come with the layout and hold for the rest of the project:

- Execution agents see only `workspaces/<task>/`, enforced by the tools, not by convention.
- Every database row points at a file; binary data never enters the database.
- The spec is the contract. Changing it is a decision, so it goes back to the user.

## What it produces

[`examples/object-detection-claude/spec/task.md`](https://github.com/hoshiori-dev/annotools/blob/main/examples/object-detection-claude/spec/task.md)
is the output of one such interview: three cat classes with include/exclude rules, a minimum box
area of 1 % of the image, a three-round correction limit, and a confidence floor. Its
[`CONTEXT.md`](https://github.com/hoshiori-dev/annotools/blob/main/examples/object-detection-claude/CONTEXT.md)
and [`config/default.json`](https://github.com/hoshiori-dev/annotools/blob/main/examples/object-detection-claude/config/default.json)
show where the rest of the answers landed.

Next: [choose a store](store.md) for what the pipeline produces.

Source: [`skills/annotation-project-interview`](https://github.com/hoshiori-dev/annotools/tree/main/skills/annotation-project-interview)
