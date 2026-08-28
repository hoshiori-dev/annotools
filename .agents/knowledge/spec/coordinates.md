# normalize_coordinates / denormalize_coordinates

<!-- --8<-- [start:user] -->

## Goal

Models answer localization questions in their own frame — Claude and Qwen2.5-VL in pixels of the image
they were shown, Gemini and Qwen3-VL in a 0–1000 space (Gemini y-first), GPT in a 0–999 space — and
perform worse when asked to normalize themselves. The storage convention is normalized 0–1, x-first,
relative to the uncropped source. These two tools do the conversion in code so an agent can ask every
model natively and store one format, including when the model looked at a `crop`.

## Interface

Tools: `normalize_coordinates`, `denormalize_coordinates` (MCP) /
`annotools.geometry.normalize_coordinates`, `annotools.geometry.denormalize_coordinates` (library).

| Parameter | Type | Default | Constraints |
|---|---|---|---|
| `coordinates` | `list[list[float]]` | — | ≥ 1 entries; each entry a flat even-length list `x, y, x, y, …` (point, box, polygon) |
| `base_width` | float | — | > 0; the frame width the entries use: preview `output_width`, or 1000 / 999 |
| `base_height` | float | — | > 0; likewise `output_height`, or 1000 / 999 |
| `crop` | `[x_min, y_min, x_max, y_max]` \| null | null | the **applied** crop reported by the preview the model saw |
| `axis_order` | `"xy"` \| `"yx"` | `"xy"` | pair order in the base frame; `yx` for Gemini's `[ymin, xmin, ymax, xmax]` |

Returns: `{"coordinates": list[list[float]]}` with the same shape as the input.

- `normalize_coordinates`: base frame (of the cropped view) → normalized source coordinates, always
  `x, y` order, each value clamped to [0, 1].
- `denormalize_coordinates`: normalized source coordinates (`x, y` order, each in [0, 1]) → base frame
  of the cropped view, written `y, x` per pair when `axis_order="yx"`; not clamped or rounded.

## Behavior

1. Validate `base_width`/`base_height` > 0 and `crop` (same rules as `PreviewOptions.crop`).
2. For each entry, split into pairs (swap when `axis_order="yx"` on the base side).
3. normalize: `x_norm = crop.x_min + x / base_width × (crop.x_max − crop.x_min)`, likewise `y`; clamp.
   denormalize: `x_base = (x − crop.x_min) / (crop.x_max − crop.x_min) × base_width`, likewise `y`.
- Error `coordinates[i]: expected an even number of values, got n` for an odd-length entry.
- Error `coordinates: base_width and base_height must be > 0` for a non-positive base.
- Error `coordinates[i]: (x, y) is outside [0, 1]` when denormalizing a value outside the range.
- Error `crop: …` from the shared crop validation.

<!-- --8<-- [end:user] -->

## Acceptance criteria

1. `test_ac1_pixel_base_normalizes`: base 384×288, `[[192, 144]]` → `[[0.5, 0.5]]`.
2. `test_ac2_crop_maps_into_source`: crop `(0.25, 0.25, 0.75, 0.75)`, base 400×300, `[[0, 0, 400, 300]]`
   → `[[0.25, 0.25, 0.75, 0.75]]`.
3. `test_ac3_round_trip`: `normalize(denormalize(v))` ≈ `v` with a crop and base 1000.
4. `test_ac4_yx_order`: `[[100, 200, 300, 400]]`, base 1000, `axis_order="yx"` → `[[0.2, 0.1, 0.4, 0.3]]`;
   denormalize emits y-first.
5. `test_ac5_clamps_out_of_range`: `[[-5, 999]]`, base 384×384 → `[[0, 1]]`.
6. `test_ac6_odd_length_raises`: the message names `coordinates[1]`.
7. `test_ac7_bad_base_raises`: non-positive base and an invalid crop raise `ValueError` naming the parameter.
8. `test_ac8_denormalize_rejects_out_of_range`.
9. `test_ac9_tools`: both tools through `Client(mcp)`, including a 0–999 (GPT-style) case; the odd-length
   error surfaces as a tool error naming `coordinates[0]`.

<!-- --8<-- [start:user2] -->

## Out of scope

Choosing the convention for a model (the `mllm-multimodal-input` skill); rotated boxes (use
`rotated_bbox_to_polygon` first, then convert the 8-number entry); rounding to integer pixels.

<!-- --8<-- [end:user2] -->

## References

issue #56; `.agents/knowledge/references/mllm-models.md` (native conventions per model);
`.agents/knowledge/spec/mcp-overview.md` (crop semantics).
