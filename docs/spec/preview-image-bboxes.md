# preview_image_bboxes

## Goal

Let an agent see its candidate bounding boxes on the preview (optionally over the grid) before writing
them to the database, so it can correct positions in a short verify-and-adjust loop.

## Interface

Tool: `preview_image_bboxes` (MCP) / `annotools.image.overlay.draw_bboxes` (library)

Parameters: `PreviewOptions`, `grid: GridOptions | null` (nested object; `null` = no grid),
`objects: list[BBoxObject]` (≥ 1), `line_width: int = 2` (≥ 1).

`BBoxObject`: `bbox: [x_min, y_min, x_max, y_max]` normalized to the uncropped source,
`label: str | null`, `color: str = "blue"` (CSS/PIL name or `#RRGGBB`).

Returns: `[Image, metadata]` with the base keys, `grid` when a grid was drawn, and `objects: int`.

## Behavior

1. Render the preview (and the grid, if given) exactly as `preview_image_grid`.
2. Map each box from source-normalized coordinates into output pixels through the crop: parts outside
   the crop are clipped; a box entirely outside is skipped (still counted in `objects`).
3. Draw the rectangle outline `line_width` px wide in `color`. With a label, draw a filled tag in
   `color` with the label text (PIL default font) just above the box's top-left corner, moved inside
   the image when it would leave the frame; text is white or black depending on the color's luminance.
4. Encode as usual.
- Error: empty `objects`, invalid box (range/order), unknown color, `line_width < 1` → `ValueError`
  naming the object index (`objects[2].bbox: …`).

## Acceptance criteria

1. `test_ac1_box_pixels`: bbox (0.1, 0.1, 0.5, 0.5) on a 768×768 white preview → blue pixels on all four
   edges at the mapped coordinates, white just inside and outside the 2 px band.
2. `test_ac2_label_rendered`: a label produces non-white pixels above the box; without a label the area
   above the box stays white.
3. `test_ac3_crop_composition`: `crop=(0.5, 0, 1, 1)` and bbox (0.5, 0, 1, 1) → outline along the output
   image border.
4. `test_ac4_colors`: `"red"` and `"#00ff00"` accepted; `"not-a-color"` → `ValueError` naming the object.
5. `test_ac5_grid_plus_boxes`: with a grid, box edge pixels are pure `color` (drawn after the grid).
6. `test_ac6_empty_objects_raises`: `objects=[]` → `ValueError`.
7. `test_ac7_tool`: via `Client(mcp)` with `grid` and two objects → metadata `objects == 2`, `grid` present.

## Out of scope

Keypoints, polygons, segmentation, filled boxes.

## References

Plan §5.2, §7 (detection loop); issue #17; `docs/spec/mcp-overview.md`.
