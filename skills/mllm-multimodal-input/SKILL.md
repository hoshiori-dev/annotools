---
name: mllm-multimodal-input
description: >-
  Chooses how to feed images, video, and audio to a multimodal model at the lowest token cost and
  with prompt-cache hits — per-model token formulas, cheapest resolutions, coordinate conventions,
  and prompt layout for Gemini, GPT, Claude, and Qwen. Use when planning a labelling or captioning
  run, picking preview sizes for annotools tools, estimating media token cost, deciding how to send
  an image (base64, URL, file id), asking why cache hits are zero, or choosing the reasoning effort
  for a batch. Not for model pricing tables or provider SDK code.
---

# MLLM Multimodal Input

Facts below were verified against vendor docs on 2026-08-27; re-verify any number you are about to
rely on for cost (vendors change tiers without notice) and record the date next to it.

## Workflow

1. **Pick the model and read its row** in the tables below; note its resolution sweet spot and the
   coordinate convention it answers in.
2. **Size the media with annotools** (`preview_image*`, `preview_video*`, `clip_audio`): set
   `max_width`/`max_height` to the sweet spot, use `crop` for detail instead of a bigger image, and
   `fps`/`max_frames` for video. Never send originals.
3. **Lay the prompt out for the cache**: static system text and tool definitions first, task rules
   second, the per-item block (metadata + media + question) last. Keep the static prefix above the
   provider minimum (table below) or nothing caches.
4. **Ask for coordinates in the model's native convention** and convert to the project's storage
   convention (normalized xyxy, `docs/spec/mcp-overview.md`) in code — never ask a model to convert.
5. **Set reasoning effort per task**: lowest tier for captioning/classification, medium for
   detection with a self-check loop, high only when the spec demands it.
6. **Verify once, then batch**: run 3 items, read `usage` (cached tokens, input tokens per image),
   compare with the estimate, then submit the rest (batch endpoints where the vendor offers 50 %).
   Done when: measured tokens per item are within 20 % of the estimate and cache reads are non-zero
   from the second request on.

## Image token cost per model (2026-08-27)

| Model family | Rule | Cheapest useful size |
|---|---|---|
| Gemini 2.5 / 3.x | ≤ 384×384 → 258 tokens; larger images are tiled: crop unit ≈ floor(min(w, h)/1.5), tiles = ceil(w/unit) × ceil(h/unit), 258 tokens per tile (768×768 → 4 tiles, 768×432 → 6). `media_resolution` low/default caps tokens per image/frame. | ≤ 384 px both sides (258 tokens); otherwise accept 4–6 tiles at 768 |
| Claude 4.7+ (high-res tier); older Claude (standard) | 28×28 patches: ⌈w/28⌉ × ⌈h/28⌉ tokens. Downscaled to ≤ 2576 px edge / 4784 tokens (high-res) or ≤ 1568 px / 1568 tokens (standard); padded to a multiple of 28 on the right/bottom. 768×768 → 784 tokens; 768×432 → 448. | Any size ≤ 1568 px; 768 long side ≈ 450–800 tokens |
| GPT-4o / GPT-4.1 / GPT-5.1 (tile models) | `detail=low` → base only (85 / 85 / 70). `high`: fit in 2048², then shortest side to 768, count 512-px tiles × (170 / 170 / 140) + base. 768×768 → 4 tiles ≈ 765 tokens; ≤ 512×512 → 1 tile ≈ 255. | ≤ 512 px both sides for 1 tile; `detail=low` when layout only |
| GPT-5.2+ / GPT-5.4 / GPT-5.6 (patch models), GPT-4.1-mini | 32-px patches: ceil(w/32) × ceil(h/32) × multiplier (1.2 for 5.4/5.6, 1.62 for 4.1-mini). 768×768 → 576 patches × 1.2 ≈ 692. | Same as above; area scales linearly |
| Qwen2.5-VL / Qwen3-VL | 14-px patches merged 2×2 → one token per 28×28 px; `min_pixels`/`max_pixels` bound the area (typical 256·28² – 1280·28²), sizes rounded to multiples of 28. 768×768 → 784 tokens. | Set `max_pixels` to the budget; 768 long side ≈ 450–800 tokens |

Practical consequence: the annotools default of 768 px on the long side costs roughly 450–800 tokens
on Claude, GPT, and Qwen and 4–6 × 258 tokens on Gemini. For Gemini, downsize to ≤ 384 px when
the task tolerates it or lower `media_resolution`; for fine detail on any model, `crop` a region at
768 px rather than sending a 1536 px image.

## Video and audio

| Provider | Video | Audio |
|---|---|---|
| Gemini | Sampled at 1 fps; 258 tokens per frame (default) or 66 (low `media_resolution`) → ≈ 300 or 100 tokens per second incl. audio | 32 tokens per second |
| Claude | No native video input: send sampled frames as images (`preview_video`, `max_frames` ≤ 20 keeps the per-image dimension limit relaxed) | No native audio input; transcribe first |
| GPT (vision models) | No native video in chat: send frames as images | Audio models accept audio separately (not the vision path) |
| Qwen2.5-VL | Native video: `fps` / `num_frames` control sampling; a total pixel budget applies across frames | Qwen-Audio family separately |

Rule: sample sparser (`fps`) before sampling smaller; 32 frames at 768 px is already 15–25 k tokens.

## Coordinate conventions the models answer in

| Model | Ask for | Convert with |
|---|---|---|
| Claude | Absolute pixel `[x1, y1, x2, y2]` of the image **as sent**; the docs state normalized 0–1000 requests work poorly. Pre-resize so no server-side resize happens (annotools previews are already ≤ 1568 px). | divide by the preview `output_size`, then map through `crop` using the annotools metadata |
| Gemini | `[ymin, xmin, ymax, xmax]` normalized to 0–1000 (note the y-first order); segmentation masks as `[x, y]` polygons 0–1000 | divide by 1000, swap to xyxy |
| GPT | No documented convention; pixel coordinates of the sent image work in practice — state the image size in the prompt | divide by `output_size` |
| Qwen2.5-VL | Absolute pixels of the resized image (the size after `min/max_pixels`) | divide by the resized size |

Store everything as normalized xyxy relative to the uncropped source (annotools convention); the
grid overlay helps every model equally because the grid is drawn on the image the model sees.

## Prompt caching minimums (prefix must be byte-identical)

| Provider | Minimum cacheable prefix | Notes |
|---|---|---|
| Claude (Opus 5 / Fable 5) | 512 tokens | Opus 4.8 / Sonnet 5 / Sonnet 4.6: 1024; Opus 4.7: 2048; Opus 4.6 / Haiku 4.5: 4096. Max 4 `cache_control` breakpoints; images count and can sit in the cached prefix. |
| OpenAI | 1024 tokens (GPT-5.6+); 2048 for older models | Automatic; rendered prefix incl. tool definitions and images; 30-minute retention on GPT-5.6+. |
| Gemini | 2048 tokens (2.5 Flash/Pro); 4096 (3.x) | Implicit caching; put large common content first; explicit caches for reuse across many runs. |
| Qwen (DashScope / self-hosted) | Provider-specific; self-hosted vLLM/SGLang prefix caching has no minimum | Keep the same layout rule. |

Layout that hits every cache: `[system: task spec, class definitions, output schema]` →
`[few-shot examples]` → **breakpoint** → `[item metadata]` → `[image(s)]` → `[question]`.
Anything that varies per item (file names, timestamps, item ids) goes after the breakpoint.

## Sending images

- Inline base64 from the annotools preview bytes is the default for single-turn batch labelling.
- Multi-turn loops (detection with self-check) re-send history: use file references where the
  provider has them (Claude Files API `file_id`, Gemini Files API, OpenAI file inputs) to keep
  payloads small; keep the loop ≤ 3 rounds.
- Put images before the question (Claude and Gemini both document image-then-text as best).

## Gotchas

- Gemini's "one tile" is ≤ 384 px, not 768 — an untested assumption that 768 fits one tile costs 4–6×.
- Claude pads to multiples of 28; normalize by the **resized** size, never the padded one.
- Any per-item text placed before the cache breakpoint (a file name in the system prompt) sets cache
  reads to zero for the whole run.
- OpenAI `detail=low` ignores resolution entirely — useless for localization, fine for captions.
- Gemini's `[ymin, xmin, …]` order is the most common silent bug when converting to xyxy.

## References

- Read [references/sources.md](references/sources.md) when you need the vendor page for a number.
