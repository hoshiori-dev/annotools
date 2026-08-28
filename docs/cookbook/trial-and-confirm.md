# Trial and confirm

Between a finished pipeline and a finished dataset there is one step: run three items, show the
output to the person who asked for it, and change the prompt until they accept it. Then run the
rest. The trial is not a smoke test — it is where the spec meets real data and loses.

Both task scaffolds put it in the same place. Captioning is linear (preview → long caption →
compress twice → tags → four writes), so its trial checks the prompts and the length budgets.
Detection runs the [correction loop](localization-loop.md), so its trial writes the final overlay to
`data/interim/trial/<item>.jpg` and shows the user that path with the box list. In both cases the
accepted outputs become the few-shot examples in the cached prefix, which is why the trial happens
before the full run rather than after it.

## What three items actually caught

The four example projects each ran `just trial 3` on COCO cat images on 2026-08-28. Three of the
four came back with a flagged item on the first pass, in two distinct ways — and neither of them was
the label being wrong:

| | [captioning-claude](https://github.com/hoshiori-dev/annotools/tree/main/examples/image-captioning-claude) | [captioning-codex](https://github.com/hoshiori-dev/annotools/tree/main/examples/image-captioning-codex) | [detection-claude](https://github.com/hoshiori-dev/annotools/tree/main/examples/object-detection-claude) | [detection-codex](https://github.com/hoshiori-dev/annotools/tree/main/examples/object-detection-codex) |
|---|---|---|---|---|
| Model | `claude-opus-5`, effort low | `gpt-5.6-terra`, effort low | `claude-opus-5`, effort medium | `gpt-5.6-terra`, effort medium |
| Items | 3 | 3 | 3 | 3 |
| `needs_review` after run 1 | 1 | 1 | 0 | 1 |
| Tokens, run 1 | 24 in / 2,108 out; 46,938 cache read, 15,482 cache creation | 560,638 in, of which 490,880 cached; 2,635 out, 943 reasoning | 24 in / 1,222 out; 60,379 cache read, 15,616 cache creation | 405,846 in, of which 331,648 cached; 1,797 out, 741 reasoning |
| Cost (USD) | 0.234 (0.078 per image) | not reported | 0.220 (0.073 per image) | not reported |
| Wall time, sequential | 69.0 s | 163.8 s | 67.1 s | 125.6 s |

The Claude columns' token fields come from each item's final result message while `cost_usd` covers
every turn of the item, so the two do not divide into each other.

The failures:

- **captioning-claude** produced an 11-word short caption against a 10-word budget, so the item
  became `needs_review`. The retry produced the same 11 words and hit the 0.25 USD per-item budget
  on the way, so it stayed `needs_review` and the export wrote 2 of 3 items. A word budget the model
  misses by one is a prompt problem, and this is the run that shows it.
- **captioning-codex** and **detection-codex** each had one item where the model ended its turn
  without recording anything. A retry (`just run`, a second run id) fixed both — all four caption
  variants recorded in one case, the box committed in one round in the other — and both exports then
  wrote 3 items. An agent that ends its turn without calling the write tool is a failure mode you
  find on item 2 or on item 600.
- **detection-claude** passed with 0 `needs_review`, 1.0 rounds per image, and 0.913 mean IoU
  against the COCO boxes.

## What the numbers are for

Two things come out of the trial that no estimate provides.

**Cost per item, measured.** 0.073–0.078 USD per image on the Claude SDK examples. Multiplied out
over the ≈ 184-image dataset that is roughly 14 USD — a derived figure, 184 × a per-image number that
is itself the SDK's client-side estimate rather than a bill, and the point at which to decide
whether to run it. The Codex SDK reports no cost at all under a subscription login (`cost_usd` is
0.0 in the summary), so that number has to come from the provider dashboard; what it does report is
token usage, and the cached share — 490,880 of 560,638 input tokens in one run, 331,648 of 405,846
in the other — is what a correct [cache layout](token-budget.md) looks like from the other side.

**That failure handling works.** Every one of these projects sets a failing item's rows to
`needs_review` rather than overwriting them, which keeps the item in `items_pending`, so a retry is
the same command with a new run id and the good items are never touched. The trial is the cheapest
place to confirm that, because the full run is where you will need it.

Wall time is measured sequentially here — `just trial` runs items one at a time; the full run uses
four workers.

A trial is done when the user accepts the output, the failure path has been exercised, and the
project's README usage record is filled with the numbers above. Then the full run, with the same
gate at the end: a completed run and the agreed `needs_review` rate.

Next: [export](export.md).

Source: [`skills/task-image-captioning`](https://github.com/hoshiori-dev/annotools/tree/main/skills/task-image-captioning)
and [`skills/task-object-detection`](https://github.com/hoshiori-dev/annotools/tree/main/skills/task-object-detection)
