# Fit the model's token budget

Media is the expensive part of an annotation run, and the size of the image you send is the only
lever that scales with the whole dataset. Two decisions belong here: how big the preview is, and
where the cache breakpoint sits. Both are per-model, both go in `config/`, and neither belongs in
code.

The rule for the first: never send an original. Send an annotools preview at the size the model
bills well at, and when detail is missing, `crop` a region at that same size rather than raising the
resolution of the whole frame.

## What an image costs

Verified against vendor documentation on 2026-08-27; the pages behind each number are listed in the
skill's [`references/sources.md`](https://github.com/hoshiori-dev/annotools/blob/main/skills/mllm-multimodal-input/references/sources.md).
Re-check anything you are about to base a budget on — vendors move tiers without notice.

--8<-- "skills/mllm-multimodal-input/SKILL.md:tokens"

The families split into two billing shapes. Gemini has a cliff, and the table above says where it
is; the other families bill by area, with no tile boundary to exploit, so a smaller image saves a
little and loses detail. This is why the annotools default of 384×384 — chosen for Gemini's cliff —
is the wrong default for most projects, and why the size belongs in `config/` rather than in code.

--8<-- "skills/mllm-multimodal-input/SKILL.md:sizes"

Set it once at registration (`ANNOTOOLS_MAX_WIDTH` / `ANNOTOOLS_MAX_HEIGHT`, or
`annotools --max-width W --max-height H`); every tool also takes `max_width`/`max_height` per call.
For a pipeline, the size lives in `config/` and is passed to the tool constructor —
see [step 5](sdk-tools.md).

## Layout for the cache

The static part of the prompt is the class definitions, the output schema, the tool definitions, and
the few-shot examples; the variable part is one item. Everything static goes first, then the cache
breakpoint, then item metadata, the image, and the question. One item id or file name placed above
the breakpoint sets cache reads to zero for the entire run — the prefix has to be byte-identical.

Each provider also has a minimum cacheable prefix — a few hundred to a few thousand tokens,
depending on the model — and below it nothing caches at all. The skill's
["Prompt caching minimums" table](https://github.com/hoshiori-dev/annotools/blob/main/skills/mllm-multimodal-input/SKILL.md)
lists the current figure per model, dated.

What this looks like when it works: the three-image trial of
[`object-detection-claude`](https://github.com/hoshiori-dev/annotools/tree/main/examples/object-detection-claude)
billed 24 uncached input tokens against 60,379 cache reads and 15,616 cache-creation tokens, with
1,222 output tokens, for 0.220 USD — 0.073 per image at a 768 px preview. Almost everything the run
reads is the static prefix, re-read on every turn at the cache rate; the per-item text is the 24.

## Measure before the full run

Estimates are for choosing; `usage` is for believing. Run three items, read the cached and input
token counts, compare with the estimate, and only then submit the rest. The target is measured
tokens per item within 20 % of the estimate and non-zero cache reads from the second request on.
That is the same three items as the [trial](trial-and-confirm.md), so it costs nothing extra.

For video, sparser beats smaller: a few dozen frames at a usable size already run into tens of
thousands of tokens, so lower the frame rate before lowering the resolution. The skill's video and
audio table has the per-provider rates.

Next: [the localization loop](localization-loop.md), where the preview size meets coordinates.

Source: [`skills/mllm-multimodal-input`](https://github.com/hoshiori-dev/annotools/tree/main/skills/mllm-multimodal-input)
