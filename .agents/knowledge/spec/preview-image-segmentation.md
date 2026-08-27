# preview_image_segmentation

## Goal

Show an instance / panoptic / semantic mask on top of the preview (optionally over the grid) so an agent
can check region extents and which ID is which, at preview size.

## Interface

Tool: `preview_image_segmentation` (MCP) / `annotools.image.segmentation.load_mask` + `overlay_mask`

Parameters: `PreviewOptions`, `grid: GridOptions | null`, plus

| Parameter | Type | Default | Constraints |
|---|---|---|---|
| `mask_source` | str | — | single-channel image (uint8/uint16 PNG or TIFF); pixel value = ID, 0 = background |
| `annotation` | `"label"` \| `"legend"` | `"label"` | label: ID text at each region; legend: strip below the image |
| `id_names` | `{id: name}` \| null | null | optional display names (JSON object keys are strings) |
| `alpha` | float | 0.5 | `[0, 1]`, blend strength of the region colour |
| `line_width` | int | 2 | ≥ 0; region outline width, 0 disables outlines |

Returns: `[Image, metadata]` with the base keys, `grid` when drawn, `ids` (number of non-zero IDs
present), and in legend mode `legend: [{"id", "name", "color"}]` plus `image_size: [w, h]` — the
image area at the top of the composite. In legend mode `output_size` is the whole composite; the
inverse mapping of `mcp-overview.md` applies to `image_size` (and `scale` refers to it).

## Behavior

1. Load the mask; it must decode to mode `L`, `P` (palette indices), `I`, or `I;16` (any byte order)
   with one channel — anything else raises `ValueError("mask_source: …")`.
2. Resize the mask to the source size (nearest neighbour) if it differs, apply exactly the pixel crop
   the image received (carried on the preview result, not re-derived from the normalized box), and
   resize to the output size (nearest). RGBA sources are flattened onto white first.
3. Colour every non-zero ID with `color_from_text(str(id))` and blend it over the image at `alpha`.
4. If `line_width > 0`, draw region boundaries (pixels whose ID differs from a 4-neighbour) in the
   region colour at full opacity, `line_width` px.
5. `label`: draw the ID (or its `id_names` entry) as a tag at the region centroid, clamped inside the
   frame. `legend`: append a strip below the image listing `swatch id name` rows (wrapping into
   columns), then re-fit the combined image inside `max_width` × `max_height` and `target_pixels`
   (plain resize of the composite); report `image_size` and rescale `scale` accordingly.
6. Grid (if any) is drawn before the mask colours.
- Error: `alpha` outside `[0, 1]`, `line_width < 0`, unknown `annotation` → `ValueError`.

## Acceptance criteria

1. `test_ac1_mask_colours_regions`: 2-ID mask on white → both regions blended toward distinct colours
   (`color_from_text("1")`/`("2")` at 50 %); background stays white.
2. `test_ac2_mask_resized_to_source`: a mask at half the source size aligns with the source regions.
3. `test_ac3_label_mode_draws_ids`: label text appears near each region centroid; `id_names` replaces
   the number.
4. `test_ac4_legend_mode_fits_limits`: output height ≤ `max_height` with the legend strip; metadata
   `legend` lists both IDs with names and colours.
5. `test_ac5_non_single_channel_raises`: an RGB mask → `ValueError` naming `mask_source`.
6. `test_ac6_tool`: via `Client(mcp)` with grid → metadata has `grid` and `ids == 2`; string-keyed
   `id_names` (`{"1": "cat"}`) are accepted.
7. `test_ac7_crop_alignment`: for crops that do not land on pixel boundaries the mask region covers
   exactly the image rows/columns it describes (no one-pixel gap).
8. `test_ac8_line_width`: `line_width=0` draws no outline; `-1` → `ValueError`.
9. `test_ac9_legend_metadata`: legend mode reports `image_size` (image area) and `scale ==
   image_size[0] / cropped source width`.

## Out of scope

RGB-encoded panoptic masks; polygonization; per-ID custom colours.

## References

issue #23; ARCHITECTURE.md Decisions (mask format); `.agents/knowledge/spec/color-from-text.md`.
