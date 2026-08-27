# preview_image_keypoints

## Goal

Show keypoint annotations as dots (with optional labels) on the preview, optionally over the grid, so an
agent can verify point placement before storing it.

## Interface

Tool: `preview_image_keypoints` (MCP) / `annotools.image.overlay.draw_keypoints` (library)

Parameters: `PreviewOptions`, `grid: GridOptions | null`, `objects: list[KeypointObject]` (≥ 1),
`point_diameter: int = 3` (≥ 1, output pixels).

`KeypointObject`: `point: [x, y]` normalized to the uncropped source, `label: str | null`,
`color: str = "blue"`.

Returns: `[Image, metadata]` with the base keys, `grid` when drawn, and `objects: int`.

## Behavior

1. Render the preview (and grid) as `preview_image_grid`.
2. Map each point through the crop; points outside the output image are skipped (still counted).
3. Draw a filled circle of `point_diameter` px centred on the mapped point. With a label, draw the same
   filled tag as bounding boxes to the right of the dot (moved inside the frame when needed).
- Error: empty `objects`, point outside `[0, 1]`, unknown color, `point_diameter < 1` → `ValueError`
  naming the object index.

## Acceptance criteria

1. `test_ac1_dot_pixels`: point (0.5, 0.5), diameter 3 on 768×768 white → blue at (384, 384) and its
   4-neighbours, white at distance 4.
2. `test_ac2_label_offset`: with a label, non-white pixels appear right of the dot and the dot centre
   stays `color`.
3. `test_ac3_out_of_range_raises`: (1.2, 0.5) → `ValueError` naming `objects[0].point`.
4. `test_ac4_crop_composition`: `crop=(0.5, 0, 1, 1)`: point (0.25, 0.5) is not drawn; (0.75, 0.5)
   lands at the output centre.
5. `test_ac5_tool`: via `Client(mcp)` → metadata `objects == 2`.

## Out of scope

Skeleton edges between keypoints; visibility flags.

## References

Plan §5.2; issue #18; `docs/spec/mcp-overview.md`; `docs/spec/preview-image-bboxes.md`.
