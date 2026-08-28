---
icon: lucide/spline
---

# Polygons

Draw COCO-style outlines and DOTA-style oriented boxes with the same 8-or-more-number flat format,
with numbered vertices so a model can correct one point instead of restating the shape.

=== "Library"

    ```python
    from annotools import (
        PolygonObject,
        RotatedBox,
        draw_polygons,
        is_rectangle,
        load_image,
        normalize_coordinates,
        preview,
        rotated_box_to_corners,
    )

    view = preview(load_image("photo.jpg"), max_width=768, max_height=768)
    width, height = view.metadata["output_size"]

    answer = [[180, 113, 454, 171, 420, 327, 146, 269]]  # 4 corners in pixels of the view
    print("rectangle:", is_rectangle(answer[0]))  # pixels are square, so the test means something here
    outline = normalize_coordinates(answer, width, height, crop=view.metadata["crop"])

    corners = rotated_box_to_corners(
        RotatedBox(cx=0.72, cy=0.68, w=0.26, h=0.24, theta=15),
        aspect_ratio=view.metadata["original_width"] / view.metadata["original_height"],
    )

    overlay = draw_polygons(
        view,
        [
            PolygonObject(points=outline[0], label="roof"),
            PolygonObject(points=corners, label="sign", color="orange"),
        ],
    )
    ```

    The test prints `True`, so that answer could be stored as a rotated box. Run it on the pixel
    answer, not on normalized coordinates: normalized units are stretched by the aspect ratio, so a
    genuine rectangle on a 4:3 image is a parallelogram there. `rotated_box_to_corners` takes
    `aspect_ratio` for the same reason, and does not clip — a box touching the border can produce
    values outside 0-1, which `draw_polygons` rejects.

=== "MCP"

    `normalize_coordinates` on the model's outline, `rotated_bbox_to_polygon` for the oriented box,
    then `preview_image_polygons` to draw both:

    ```json
    {
      "coordinates": [[180, 113, 454, 171, 420, 327, 146, 269]],
      "base_width": 768,
      "base_height": 576,
      "crop": [0, 0, 1, 1]
    }
    ```

    ```json
    {
      "boxes": [{ "cx": 0.72, "cy": 0.68, "w": 0.26, "h": 0.24, "theta": 15 }],
      "angle_unit": "degrees",
      "aspect_ratio": 1.3333
    }
    ```

    ```json
    {
      "source": "photo.jpg",
      "objects": [
        { "points": [0.2344, 0.1962, 0.5911, 0.2969, 0.5469, 0.5677, 0.1901, 0.467], "label": "roof" },
        { "points": [0.618, 0.519, 0.869, 0.609, 0.822, 0.841, 0.571, 0.751], "label": "sign" }
      ],
      "max_width": 768,
      "max_height": 768
    }
    ```

    `aspect_ratio` is the source's `original_width / original_height` from any preview's metadata —
    1600/1200 here — and leaving it at the default 1.0 shears the box on a non-square image. Both
    conversions answer with full-precision numbers, rounded above for readability. The overlay
    returns the image plus metadata with `objects`; vertex indices are 1-based and drawn unless
    `show_point_index` is turned off, which is what lets a correction round say "move point 3 left"
    instead of resending eight numbers. There is no MCP tool for the rectangle test — deciding
    whether a 4-point answer can collapse into a rotated box is a library-side call.

**Then**: [`preview_image_polygons`](../mcp/tools.md#preview_image_polygons) and
[`rotated_bbox_to_polygon`](../mcp/tools.md#rotated_bbox_to_polygon) for the parameters;
[`draw_polygons`](../api/image.md#annotools.image.overlay.draw_polygons),
[`rotated_box_to_corners`](../api/geometry.md#annotools.geometry.rotated_box_to_corners) and
[`is_rectangle`](../api/geometry.md#annotools.geometry.is_rectangle) for the library contract.
Choosing between a polygon and a rotated box, and the correction loop, are in
[`skills/localization-annotation-guide`](https://github.com/hoshiori-dev/annotools/tree/main/skills/localization-annotation-guide);
committing the accepted shapes is [`skills/sqlite-annotation-store`](https://github.com/hoshiori-dev/annotools/tree/main/skills/sqlite-annotation-store).
