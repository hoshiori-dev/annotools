# MLLM Token Budget for Media Input

Load this when choosing preview sizes, grid density, frame rates, or explaining why a default exists.

## Source Of Truth

`references/mllm-models.md` holds the vendor facts (dated, with URLs); this file records only the
project decisions built on them. Update the reference first when a figure drifts.

## Decisions

- Default preview: fit within 768×768, downscale only (project decision, 2026-08-27). Rationale as
  decided: one Gemini 768×768 tile; other frontier models size tokens by pixel area without tiling at
  that size. **Verification note (Gemini docs, 2026-08-27):** the documented rule is 258 tokens when both
  dimensions are ≤ 384 px; otherwise the image is tiled with crop unit ≈ floor(min(w, h) / 1.5) and
  tiles = ceil(w / unit) × ceil(h / unit) at 258 tokens each — so a 768×432 preview costs 6 tiles
  (1548 tokens) and a 768×768 one 4 tiles, while ≤ 384×384 costs 258. For Gemini the cheap point is
  therefore ≤ 384 px on both sides (or the model's `media_resolution` setting), not 768. Keep 768 as the
  default until the user revisits it; per-model sweet spots are in `references/mllm-models.md` and the
  `mllm-multimodal-input` skill, and tools accept `max_width`/`max_height` per call.
- Crop-zoom instead of upscaling: `crop` on a preview tool re-renders a region at up to 768 px, giving
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
