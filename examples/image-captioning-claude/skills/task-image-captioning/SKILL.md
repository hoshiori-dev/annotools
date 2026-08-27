---
name: task-image-captioning
description: >-
  Scaffolds an image-captioning project — requirement checklist (length budget, focus order,
  language, forbidden content, variants such as long/medium/short/tags), prompt templates, the
  trial-label-and-confirm step, a linear parallel pipeline skeleton, and export. Use when asked to
  caption, describe, or tag a set of images, when an interview settled on the captioning family, or
  when a captioning pipeline needs its prompts or pipeline skeleton. Not for localization tasks
  (boxes, masks) and not for the interview itself.
---

# Task scaffold: image captioning

Captioning is linear: one preview per image, one model call (or a short chain for variants), one
write. No grid, no correction loop; the cost lever is preview size and prompt caching.

## Workflow

1. **Confirm the requirement checklist** (from the `annotation-project-interview` skill's captioning
   branch): length budget per variant, focus order, language and register, forbidden content, tag
   vocabulary (open or fixed), reasoning effort (lowest tier), batch vs. online.
2. **Prompts** from [assets/prompts/long.md](assets/prompts/long.md),
   [assets/prompts/compress.md](assets/prompts/compress.md) (long → medium → short by successive
   compression) and [assets/prompts/tags.md](assets/prompts/tags.md); the system part is static
   (cached), the item part carries only the image and its id.
3. **Trial**: run 1–3 images with `look_at_item` at the agreed preview size, show the image (or its
   path) with each variant to the user, adjust prompts, repeat until accepted. Record the accepted
   examples as few-shots in the cached prefix.
4. **Pipeline** from [assets/pipeline_skeleton.py](assets/pipeline_skeleton.py): items from
   `items_pending`, N workers, per item: preview → long → compress ×2 → tags → four
   `record_annotation` calls (`kind=caption`, `key=long|medium|short`; `kind=tag`), status `final`;
   on any failure every row of the item in this run is set to `needs_review` and an error row
   (`key=error`) is added, so the item stays pending and nothing good is overwritten.
5. **Export**: `export.py --format jsonl` gives one line per image with the four annotations; map to
   the project's field names in a small post-step if the consumer wants flat keys.
   Done when: the trial passed, a full run finished with ≤ 1 % `needs_review`, and the README's usage
   record (tokens, cost, wall time, model) is filled.

## Gotchas

- Compressing from the long caption keeps variants consistent; generating each variant from the
  image separately produces contradictions.
- Put the length budget in tokens or characters, not "sentences" — models miscount sentences.
- Gemini bills ≤ 384 px images as one unit; captioning rarely needs more (see
  `mllm-multimodal-input`).
- Batch endpoints halve cost but delay results; use them for the full run, not the trial.
