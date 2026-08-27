# preview_image_polygons

## Goal

Preview polygons — COCO-style segmentation outlines or DOTA-style rotated boxes given as 4 corners — with
vertex dots and 1-based vertex indices, so an agent can verify both shape and vertex order.

## Interface

Tool: `preview_image_polygons` (MCP) / `annotools.image.overlay.draw_polygons` (library)

Parameters: `PreviewOptions`, `grid: GridOptions | null`, `objects: list[PolygonObject]` (≥ 1),
`line_width: int = 2`, `point_diameter: int = 3`, `show_point_index: bool = true`.

`PolygonObject`: `points: [x1, y1, x2, y2, …]` (flat, even count, ≥ 3 points, normalized to the
uncropped source), `label: str | null`, `color: str = "blue"`.

Returns: `[Image, metadata]` with the base keys, `grid` when drawn, and `objects: int`.

## Behavior

1. Render the preview (and grid) as `preview_image_grid`.
2. Map every vertex through the crop; draw the closed outline `line_width` px wide (PIL clips segments
   outside the frame). A polygon with every vertex outside the frame is skipped (still counted).
3. Draw a dot of `point_diameter` at each vertex; when `show_point_index` is true, draw the 1-based
   index as a tag next to the vertex, offset away from the polygon centroid.
4. With a label, draw the label tag at the first vertex.
- Error: empty `objects`, odd number of values or fewer than 3 points, a value outside `[0, 1]`,
  unknown color, `line_width`/`point_diameter < 1` → `ValueError` naming the object index.

## Acceptance criteria

1. `test_ac1_outline_and_vertices`: triangle (0.1,0.1), (0.5,0.1), (0.1,0.5) on 768×768 white →
   `color` pixels at the segment midpoints and at each vertex; white at the triangle centroid.
2. `test_ac2_point_indices`: with indices, non-white pixels near each vertex beyond the dot radius;
   with `show_point_index=False` the vertex neighbourhood outside the dot stays white.
3. `test_ac3_odd_count_raises`: 5 values → `ValueError` mentioning `objects[0].points`; 2 points → same.
4. `test_ac4_rotated_box_roundtrip`: the 4 corners of an axis-aligned box (0.2,0.2)-(0.6,0.4) render an
   outline whose edge midpoints are `color`.
5. `test_ac5_tool`: via `Client(mcp)` with `grid` → metadata `objects == 1`, `grid` present.

## Out of scope

Filled polygons; segmentation masks (own spec); rotated-box conversion (`rotated_bbox_to_polygon`, P2).

## References

issue #19; `.agents/knowledge/spec/mcp-overview.md`; `.agents/knowledge/spec/preview-image-keypoints.md`.
