---
name: annotation-project-interview
description: >-
  Interviews the user to consensus on a multimodal annotation project — design-tree rounds over task
  family, classes and rules, output format, model and input method, quality control, correction
  rounds, budget — then scaffolds the workspace with its invariants. Use when asked to label,
  annotate, caption, detect, segment, or build a dataset from images, video, or audio and no spec
  exists yet, when a labelling brief is vague, or when starting an example annotation project. Not
  for running an existing pipeline or for projects whose spec/ is already agreed.
---

# Annotation Project Interview

The interview is a design tree: every settled decision unlocks the questions that depend on it. Ask
the whole frontier of unblocked questions in one numbered round with one recommendation each, wait,
recompute, repeat — read [references/design-tree.md](references/design-tree.md) when running a round
(frontier rule, numbering, what counts as a fact vs. a decision, when the tree is done). Facts (file
counts, image sizes, available models, existing data) are yours to look up; decisions are the user's.

## Workflow

1. **Frame** the subject in one exchange: what data, what the labels are for (training a model?
   evaluation? search?), who consumes the output, and which agent SDK will run the pipeline.
2. **Round 1 — the trunk** (ask all at once; recommendations in brackets):
   1. Task family: captioning / detection / keypoints / polygons / segmentation / rotated boxes /
      video events / audio segments [infer from the brief].
   2. Source data location and mutability [`workspaces/<task>/data/raw`, read-only, download
      script].
   3. Target output format: jsonl / csv / parquet / webdataset tar / COCO json [jsonl].
   4. Model and provider for the execution agent [the user's default; consequences from
      `mllm-multimodal-input`: preview size, coordinate convention, cache minimum].
   5. Budget: max cost or tokens per item, total items, parallelism [state a number].
   6. Quality bar: what makes an item acceptable, who reviews, sample rate for a second pass [5 %].
   7. Language of labels/captions and of the spec [English unless the data is language-specific].
   8. Existing labels, few-shot examples, or a style reference the user can supply [none; the trial
      round produces the first examples].
3. **Round 2 — the branches** — read [references/task-branches.md](references/task-branches.md)
   and ask only the branch for the chosen task family (caption length budget and focus order;
   class list with include/exclude rules and confusable pairs; keypoint skeleton; mask type;
   rotated-box angle convention; video sampling; audio segmentation rules), plus the shared
   items: correction-round limit for localization [3], preview size per model, tie-breaking rules.
4. **Trial-label** 1–3 items by hand with the agreed prompt (use the annotools previews; show the
   image or its path with the result) and ask for corrections. Repeat until the user accepts.
   Done when: the user says the trial output is what they want.
5. **Write the spec and scaffold** only after consensus: `spec/task.md` from
   [assets/spec-template.md](assets/spec-template.md), `CONTEXT.md` from
   [assets/context-template.md](assets/context-template.md), the layout below, and the
   `justfile` from [assets/justfile](assets/justfile). Then hand off to the `sqlite-annotation-store`
   skill (schema) and the task scaffold skills (`task-image-captioning`, `task-object-detection`) of
   this catalog.

## Project layout and invariants

```text
<project>/
  CONTEXT.md            agent entry for this project (not AGENTS.md)
  spec/                 task.md (goal, classes, output contract, QC), prompts/
  config/               model, effort, budget, parallelism (one file per environment)
  template/             workspace template copied per dataset
  skills/               skills the execution agent may load
  src/                  pipeline code (SDK agent, tools, export)
  scripts/              download / init / export entrypoints
  workspaces/<task>/
    data/raw/<name>/    read-only inputs; only scripts or humans write here
    data/interim/<name>/ previews, intermediate files
    data/dataset.db     the SQLite store (file pointers only, never blobs)
    output/             exported artefacts
  justfile              init, trial, run, export, check
```

- Execution agents see only `workspaces/<task>/`; tool allowlists enforce it.
- Every item in the DB points at a file (path or fsspec URL); binary data never enters the DB.
- The spec is the contract: prompts, tools, and export all cite it; changes go through the user.

## Gotchas

- Asking "what classes do you want" without proposing a list stalls the interview; propose from the
  data (sample 20 items, look at them with `preview_image_grid`).
- Preview size is a per-model decision (Gemini ≤ 384 px is one unit; Claude/GPT/Qwen ~450–800 tokens
  at 768) — put it in `config/`, not in code.
- A correction-round limit that the user never confirmed becomes an unbounded loop in production.
- Do not scaffold before the trial passes; a wrong spec in `spec/` propagates into every prompt.
