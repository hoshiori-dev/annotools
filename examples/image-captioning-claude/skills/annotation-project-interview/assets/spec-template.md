# <task name> — task specification

## Goal
<what the labels are for; who consumes them>

## Inputs
- Source: `workspaces/<task>/data/raw/<name>/` (<count> items, <format>, typical size <w×h>)
- Read-only; populated by `scripts/download_<name>.py`

## Labels
<class list with definitions, include/exclude rules, confusable pairs — or caption rules: length, focus order, language>

## Model and input
- Model: <id>; provider: <name>; reasoning effort: <tier>
- Preview: `max_width`/`max_height` <px>; grid <cols×rows>; coordinate convention requested: <pixels | gemini-1000>
- Prompt layout: static spec + examples (cached) → item metadata → image(s) → question

## Procedure
<linear (captioning) or grid → propose → verify → correct (≤ N rounds) → commit>

## Quality control
- Accept when: <criteria>
- `needs_review` when: <criteria>
- Second pass: <sample rate>, <how disagreements are logged>

## Output contract
- Store: `workspaces/<task>/data/dataset.db` (schema: `sqlite-annotation-store`)
- Export: `output/<name>.<jsonl|csv|parquet|tar>` — fields: <list>

## Budget
- Per item ≤ <tokens/cost>; total ≤ <cost>; parallelism <n>; stop after <k> failures
