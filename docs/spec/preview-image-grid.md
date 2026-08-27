# preview_image_grid

## Goal

Overlay a semi-transparent grid on a preview so an MLLM can anchor positions to cells; 10×10 by default
(9 lines each way), which evidence suggests improves localization without occluding content.

## Interface

Tool: `preview_image_grid` (MCP) / `annotools.image.grid.draw_grid` (library)

Parameters: `PreviewOptions` plus `GridOptions` (flattened: `columns`, `rows`, `mode`, `column_width`,
`row_width`, `color`, `opacity`, `line_width`) from `docs/spec/mcp-overview.md`.

Returns: `[Image, metadata]` with the base keys plus
`grid: {"columns": int, "rows": int, "step_x": float, "step_y": float}` where `step_*` is the cell size
in normalized coordinates of the **cropped** view (so `1 / columns` in ratio mode).

## Behavior

1. Render the preview exactly as `preview_image`.
2. Compute line positions in output pixels: ratio mode → `i × width / columns` for `i = 1..columns−1`
   (same for rows); fixed mode → multiples of `column_width` / `row_width` inside the image; the
   resulting cell counts are reported as `columns` / `rows`.
3. Draw each line `line_width` px wide, centred on the position, blended with `opacity`: `white` and
   `black` blend toward that color; `invert` blends toward the per-pixel inverse of the image.
4. Encode as usual.
- Error: `columns`/`rows` < 1, `opacity` outside `[0, 1]`, `line_width` < 1 → `ValueError`.
- Error: `mode="fixed"` without both widths, or a width < 1 → `ValueError("column_width/row_width …")`.

## Acceptance criteria

1. `test_ac1_default_grid_line_positions`: 768×768 white preview → pixels at x = round(76.8·i) for
   i = 1..9 are unchanged (white on white) while on a black image they are 50 % grey; 9 vertical and 9
   horizontal lines, no line on the borders.
2. `test_ac2_fixed_mode`: `mode="fixed", column_width=100, row_width=100` on 768×512 → lines every
   100 px; metadata `grid.columns == 8`, `grid.rows == 6`.
3. `test_ac3_color_black_and_invert`: on a white image `black` lines are 50 % grey; `invert` on a
   red image yields the blend of red and cyan.
4. `test_ac4_opacity_zero_is_noop`: `opacity=0` → identical bytes to the plain preview.
5. `test_ac5_invalid_options`: `columns=0`, `opacity=1.5`, fixed mode without widths → `ValueError`.
6. `test_ac6_tool_metadata`: via `Client(mcp)` the metadata carries `grid` with `step_x == 0.1`.

## Out of scope

Row/column index labels; overlays (own specs).

## References

Plan §5.1–5.2; issue #16; `.agents/knowledge/mllm-token-budget.md`.
