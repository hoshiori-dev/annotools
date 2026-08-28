# preview_image

<!-- --8<-- [start:user] -->

## Goal

Return an image at a size an MLLM can read within a bounded token budget, optionally zoomed into a
region, so an agent never has to load a full-resolution asset to look at it.

## Interface

Tool: `preview_image` (MCP) / `annotools.image.preview.preview` + `encode` (library)

Parameters: exactly `PreviewOptions` from `.agents/knowledge/spec/mcp-overview.md`.

Returns: `[Image, metadata]` with the base metadata keys.

## Behavior

1. Load `source` through fsspec; apply EXIF orientation; record `original_size`.
2. If `crop` is given, validate it and crop to the pixel box (rounded outward so the region is never
   smaller than requested).
3. Compute the output size: start from the cropped size; scale down to fit `max_width` × `max_height`
   and, if given, `target_pixels`; scale up only when `allow_upscale` is true and the cropped image is
   smaller than the limits (the same fit rule, applied upward). Aspect ratio is preserved; sizes are
   rounded to integers ≥ 1.
4. Resize with Lanczos (down) / bicubic (up); encode as `output_format` (JPEG q90, alpha flattened on
   white); optionally write to `save_to`.
- Error: `crop` outside `[0, 1]` or non-increasing → `ValueError("crop: …")`.
- Error: `max_width`, `max_height`, `target_pixels` < 1 → `ValueError`.
- Error: missing source → `FileNotFoundError`; other read failures → `OSError`; undecodable content →
  `ValueError`; all name the URI.
- EXIF orientation is applied on load (a rotated-by-tag portrait reports its display size).

<!-- --8<-- [end:user] -->

## Acceptance criteria

1. `test_ac1_downscale_fits_limits`: 4000×3000 → 384×288 with the default settings; for every width in
   769–4607 the long side is exactly 768 at `max_width=768` (`test_fit_size_hits_limit_exactly`).
2. `test_ac2_no_upscale_by_default`: 300×200 → 300×200; `allow_upscale=True` → 384×256 (768×576 with
   `max_width=max_height=768`).
3. `test_ac3_target_pixels`: `target_pixels=100_000` on 4000×3000 → area ≤ 100 000 and within `max_*`.
4. `test_ac4_crop_normalized`: `crop=(0.25, 0.25, 0.75, 0.75)` on 800×600 → 400×300; metadata `crop`
   echoes the box and `scale` is 1.0. `test_ac4b_crop_reports_applied_box`: a crop that does not fall on
   pixel boundaries reports the outward-rounded box and a `scale` consistent with it.
5. `test_ac5_invalid_crop_raises`: `(0.5, 0, 0.5, 1)` and `(0, 0, 1.2, 1)` → `ValueError` mentioning `crop`.
6. `test_ac6_fsspec_source`: `file://` and `memory://` URIs load; missing URI → `FileNotFoundError`;
   a directory → `OSError` naming it; a non-image file → `ValueError` naming it.
7. `test_ac7_tool_returns_image_and_metadata`: `Client(mcp).call_tool("preview_image", {...})` → image
   block with `image/jpeg` then a JSON text block with the documented keys.
8. `test_ac8_save_to_writes_file`: `save_to` produces a file whose bytes equal the returned image.

<!-- --8<-- [start:user2] -->

## Out of scope

Grids, overlays, video frames (own specs).

<!-- --8<-- [end:user2] -->

## References

issue #15; `.agents/knowledge/mllm-token-budget.md`.
