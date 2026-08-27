# MLLM Token Budget for Media Input

Load this when choosing preview sizes, grid density, frame rates, or explaining why a default exists.

## Source Of Truth

`references/mllm-models.md` holds the vendor facts (dated, with URLs); this file records only the
project decisions built on them. Update the reference first when a figure drifts.

## Decisions

- Default preview: fit within 384×384, downscale only (project decision, 2026-08-27, replacing the
  earlier 768 default). 384 is the largest size Gemini bills as one 258-token unit; a 768×768 preview is
  4 Gemini tiles and 768×432 is 6 (`references/mllm-models.md`). Models that bill by area (Claude 28-px
  patches, GPT 32-px patches, Qwen) lose detail at 384 for no saving, so deployments serving them raise
  the limit at startup (`annotools --max-width 768 --max-height 768` or `ANNOTOOLS_MAX_WIDTH=768`);
  per-model recommendations live in `skills/mllm-multimodal-input`. Every default is a
  `annotools.config.Settings` field (flags > env > built-in) and tools accept `max_width`/`max_height`
  per call.
- Crop-zoom instead of upscaling: `crop` on a preview tool re-renders a region at up to the configured limit, giving
  detail without paying for the whole image at high resolution.
- Grid default 10×10 (9 lines each way), 50 % white: dense enough to anchor coordinates, sparse enough
  not to occlude; adjust per task rather than globally.
- Video default 1 fps with a `max_frames` cap (32): frames are billed like images; sample sparser
  before sampling smaller.
- Prompt caching: keep static instructions and tool schemas first, put per-item metadata and media last
  so batch runs share the longest possible cached prefix. Per-provider minimum cacheable prefix lengths
  are in `references/mllm-models.md`.

## Per-model facts

See `references/mllm-models.md`. Two facts shape this project: Claude answers localization in pixel
coordinates of the image it saw, Gemini in `[ymin, xmin, ymax, xmax]` × 1000 — so ask each model in its
native convention and normalize in code (`skills/localization-annotation-guide`); and Gemini bills any
image ≤ 384 px on both sides as one 258-token unit.
