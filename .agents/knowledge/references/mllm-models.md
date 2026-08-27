# MLLM Reference: Per-Model Facts

External facts only, each with the verification date and the vendor page. Project decisions built on
them live in `mllm-token-budget.md` and `ARCHITECTURE.md`; the published skill
`skills/mllm-multimodal-input` is derived from this file. When a figure drifts, update here first, then
the derived copies (see the Keep In Sync table in `AGENTS.md`).

## Claude (Anthropic)

| Fact | Detail | Source (verified) |
|---|---|---|
| Image tokens | one token per 28×28 px patch: `⌈w/28⌉ × ⌈h/28⌉`; cost grows with area | Vision — https://platform.claude.com/docs/en/build-with-claude/vision (2026-08-27) |
| Resolution tiers | standard: edge ≤ 1568 px and ≤ 1568 tokens; high-resolution (Claude 4.7+): edge ≤ 2576 px and ≤ 4784 tokens; larger images are resized to fit, then padded to a multiple of 28 on the right/bottom | Vision; Coordinates and bounding boxes — https://platform.claude.com/docs/en/build-with-claude/vision-coordinates (2026-08-27) |
| Coordinate convention | "Claude works best with absolute pixel coordinates. Ask for them explicitly in your prompt … Claude does not work well when you ask for normalized coordinates, for example: 'Return bounding box coordinates between 0 and 1000.' Always ask for pixel coordinates and normalize in your own code if you need to." Coordinates refer to the image **as Claude sees it** (after its resize); "Always normalize or rescale by the resized dimensions, not the padded dimensions." | Coordinates and bounding boxes (2026-08-27) |
| Precision advice | pre-resize to the tier size so coordinates map one-to-one; crop and send the region for small targets; `transformations: {"oversized_image": "error"}` turns a silent resize into a 400 | Coordinates and bounding boxes (2026-08-27) |
| Video / audio | no native video or audio input; send sampled frames as images | Vision (2026-08-27) |
| Prompt cache minimum | Opus 5 / Fable 5: 512 tokens; Opus 4.8 / Sonnet 5 / Sonnet 4.6: 1024; Opus 4.7: 2048; Opus 4.6 / Haiku 4.5: 4096; max 4 `cache_control` breakpoints; images count toward the prefix | https://platform.claude.com/docs/en/build-with-claude/prompt-caching (2026-08-27) |

## Gemini (Google)

| Fact | Detail | Source (verified) |
|---|---|---|
| Image tokens | "258 tokens if both dimensions <= 384 pixels"; otherwise "tiled into 768x768 pixel tiles, each costing 258 tokens" with crop unit ≈ `floor(min(w, h) / 1.5)`, tiles = `ceil(w / unit) × ceil(h / unit)`; worked example 960×540 → unit 360 → 3×2 = 6 tiles = 1548 tokens. Applying the formula: 768×768 → 4 tiles, 768×432 → 6 | Image understanding — https://ai.google.dev/gemini-api/docs/image-understanding (2026-08-27) |
| `media_resolution` | low/default settings cap tokens per image and per video frame | Image understanding (2026-08-27) |
| Coordinate convention | object detection returns `box_2d` as "[ymin, xmin, ymax, xmax] normalized to 0-1000"; "You need to descale these coordinates based on your original image size"; segmentation masks as `[x, y]` polygons in the same 0–1000 space | Image understanding, object detection section (2026-08-27) |
| Video / audio | video sampled at 1 fps, 258 tokens per frame (66 at low `media_resolution`); audio 32 tokens per second | https://ai.google.dev/gemini-api/docs/video-understanding (2026-08-27) |
| Prompt cache minimum | implicit caching from 2048 tokens (2.5 Flash/Pro) or 4096 (3.x); explicit caches for reuse across runs | https://ai.google.dev/gemini-api/docs/caching (2026-08-27) |

## OpenAI GPT (and Codex)

| Fact | Detail | Source (verified) |
|---|---|---|
| Patch models | `gpt-5.6*`, `gpt-5.5`, `gpt-5.4*`, `gpt-5.2`, `gpt-4.1-mini` and similar: 32×32 px patches, `ceil(w/32) × ceil(h/32)` (scaled down proportionally when over the patch budget), multiplied by a per-model factor (1.2 for 5.x; 1.62 for 4.1-mini) and rounded up | Images and vision — https://developers.openai.com/api/docs/guides/images-vision (2026-08-27) |
| Tile models | `gpt-5.1`, `gpt-4o`, `gpt-4.1`, `gpt-4o-mini`: fit within 2048×2048, shortest side to 768, count 512-px tiles: base + per-tile tokens (85 + 170 for 4o/4.1; 70 + 140 for 5.1); `detail=low` = base tokens only | Images and vision (2026-08-27) |
| Resize advice | "For coordinate-sensitive tasks, resize images to fit those limits before sending and map returned coordinates back to the original image." | Images and vision (2026-08-27) |
| Coordinate convention | GPT-5.4 tips: "For localization tasks (including bounding boxes), provide access to code interpreter as well as a strict coordinate contract like `[x_min, y_min, x_max, y_max]` and a fixed coordinate space such as `0..999` with the origin in the top-left corner." Pixels of the sent image also work in practice but are not the documented recommendation | https://developers.openai.com/cookbook/examples/multimodal/document_and_multimodal_understanding_tips (2026-08-27) |
| Video / audio | no native video in the chat path (send frames); audio through the audio models, not the vision path | Images and vision (2026-08-27) |
| Prompt cache minimum | 1024 tokens (GPT-5.6+), 2048 for older models; automatic; 30-minute retention on GPT-5.6+ | https://developers.openai.com/api/docs/guides/prompt-caching (2026-08-27) |
| Codex | Codex (CLI/SDK) calls the same GPT models with the same image encoding, so the GPT rows apply | https://github.com/openai/codex (2026-08-27) |

## Qwen-VL (Alibaba)

| Fact | Detail | Source (verified) |
|---|---|---|
| Qwen2.5-VL tokens | 14-px patches merged 2×2 → one token per 28×28 px; `min_pixels` / `max_pixels` bound the area; sizes rounded to multiples of 28 (`smart_resize`) | https://github.com/QwenLM/Qwen2.5-VL (2026-08-27) |
| Qwen2.5-VL coordinates | "directly represents coordinates such as detection boxes and points using the actual size scale of the image, without performing traditional coordinate normalization" — absolute pixels of the resized input | https://qwenlm.github.io/blog/qwen2.5-vl/ (2026-08-27) |
| Qwen3-VL tokens | 16-px patches merged 2×2 → one token per 32×32 px; sizes rounded to multiples of 32; video `fps` default 2; `total_pixels` default differs between README and `vision_process.py` — set it explicitly | https://github.com/QwenLM/Qwen3-VL (README; `qwen-vl-utils/src/qwen_vl_utils/vision_process.py`) (2026-08-27) |
| Qwen3-VL coordinates | relative 0–1000 `[x1, y1, x2, y2]` (top-left, bottom-right); some cookbook utilities rescale with 999 as the denominator | Qwen3-VL cookbooks `2d_grounding.ipynb`, `spatial_understanding.ipynb` (2026-08-27) |
| Video | native video input; `fps` / `num_frames` sampling with a total pixel budget across frames | Qwen2.5-VL / Qwen3-VL READMEs (2026-08-27) |

## Known contradictions (record, do not resolve silently)

- Gemini: the page says larger images are "tiled into 768x768 pixel tiles", yet its crop-unit formula
  and worked example make a 768×768 image 4 tiles. The formula is what the example uses; measure
  `usage` once per model.
- OpenAI: the GPT-5.4 tips recommend a fixed `0..999` space, while the images guide talks about mapping
  pixel coordinates back after a resize. The project follows the tips (0..999) for GPT/Codex and keeps
  pixels as a documented alternative.
- Qwen2.5-VL (absolute pixels) and Qwen3-VL (0–1000 relative) differ; check the model generation before
  choosing the prompt wording.
