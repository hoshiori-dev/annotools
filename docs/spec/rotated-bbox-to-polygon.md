# rotated_bbox_to_polygon

## Goal

Turn rotated detections `(cx, cy, w, h, theta)` into the DOTA-style 8-number corner lists that
`preview_image_polygons` renders and that SQLite exports store, and let agents verify that a 4-point
polygon is actually a rectangle.

## Interface

Tool: `rotated_bbox_to_polygon` (MCP) / `annotools.geometry.rotated_box_to_corners` and
`annotools.geometry.is_rectangle` (library)

| Parameter | Type | Default | Constraints |
|---|---|---|---|
| `boxes` | list of `{cx, cy, w, h, theta}` | — | ≥ 1; `cx`, `cy` in [0, 1]; `w`, `h` > 0 (normalized) |
| `angle_unit` | `"degrees"` \| `"radians"` | `"degrees"` | applies to every `theta` |
| `aspect_ratio` | float | 1.0 | source `width / height`; > 0 |

Returns (structured): `{"polygons": [[x1, y1, x2, y2, x3, y3, x4, y4], ...]}` — one entry per box,
corners in clockwise image order starting at the top-left corner of the unrotated box, normalized to
the same frame as the input.

## Behavior

1. `theta` is the clockwise rotation (image coordinates, y down) of the box about its centre;
   `angle_unit="radians"` converts first. This matches DOTA/mmrotate `le90` after their own conversion
   to degrees; the spec does not normalize the angle range.
2. Rotation happens in an isotropic frame: x is scaled by `aspect_ratio` before rotating and divided
   afterwards, so a box on a non-square image rotates without shearing. With the default 1.0 the
   result is exact only for square sources.
3. Corners may fall outside [0, 1]; they are returned unclipped. `preview_image_polygons` rejects such
   coordinates, so callers clamp or shrink border boxes before previewing (a `clip` option is a possible
   follow-up).
4. `is_rectangle(points, angle_tol_deg=2.0, length_tol=0.02)`: true when the polygon has 4 points,
   adjacent edges are perpendicular within `angle_tol_deg`, and opposite edges have equal length within
   `length_tol` (relative).
- Error: empty `boxes`, `w`/`h` ≤ 0, `cx`/`cy` outside [0, 1], `aspect_ratio` ≤ 0 → `ValueError` naming
  `boxes[i].<field>` or the parameter.

## Acceptance criteria

1. `test_ac1_zero_angle`: (0.5, 0.5, 0.4, 0.2, 0) → [0.3, 0.4, 0.7, 0.4, 0.7, 0.6, 0.3, 0.6].
2. `test_ac2_ninety_degrees`: theta 90 → the corners of a 0.2 × 0.4 box, starting at the rotated
   top-left (0.6, 0.3).
3. `test_ac3_radians`: `angle_unit="radians"`, theta π/2 → identical to AC2.
4. `test_ac4_is_rectangle`: every output passes `is_rectangle`; a skewed quadrilateral fails; a
   3-point polygon fails.
5. `test_ac5_aspect_ratio`: with `aspect_ratio=2` a 45° box's corners, once scaled back to pixels,
   form a rectangle; with 1.0 they do not.
6. `test_ac6_tool`: structured output `polygons` with 8 numbers per box; invalid `w` → tool error
   naming `boxes[0].w`.

## Out of scope

Polygon → rotated box conversion; angle-range normalization.

## References

Plan §5.3, decision #5; issue #25; `docs/spec/preview-image-polygons.md`.
