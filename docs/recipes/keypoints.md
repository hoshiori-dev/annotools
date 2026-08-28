---
icon: lucide/circle-dot
---

# Keypoints

Collect named points — joints, landmarks, part locations — from a model that answers in a fixed
0-1000 space, and draw them back as dots for verification.

=== "Library"

    ```python
    from annotools import KeypointObject, draw_keypoints, load_image, normalize_coordinates, preview

    view = preview(load_image("photo.jpg"), max_width=768, max_height=768)
    answer = [[420, 330], [500, 375]]  # Gemini writes [y, x] in a 0-1000 space
    points = normalize_coordinates(answer, 1000, 1000, axis_order="yx")

    names = ["left_eye", "nose"]
    overlay = draw_keypoints(
        view,
        [KeypointObject(point=point, label=name) for point, name in zip(points, names, strict=True)],
        point_diameter=5,
    )
    ```

    `points` is `[[0.33, 0.42], [0.375, 0.5]]` — x first, whatever order the model used, because
    `axis_order` describes the model's frame only. The base is `1000, 1000` even on a 4:3 image: the
    0-1000 space is per axis, not a square pixel grid. `point_diameter` is in output pixels, so a
    768 px view wants a larger dot than the default 3.

=== "MCP"

    `normalize_coordinates` on the answer, then `preview_image_keypoints`:

    ```json
    {
      "coordinates": [[420, 330], [500, 375]],
      "base_width": 1000,
      "base_height": 1000,
      "axis_order": "yx"
    }
    ```

    ```json
    {
      "source": "photo.jpg",
      "objects": [
        { "point": [0.33, 0.42], "label": "left_eye" },
        { "point": [0.375, 0.5], "label": "nose" }
      ],
      "point_diameter": 5,
      "max_width": 768,
      "max_height": 768
    }
    ```

    The overlay returns the image plus the usual metadata with `objects` — the number of points
    drawn — and `grid` when a `grid` object is passed. For a model that answers in pixels of the
    preview instead, use its `output_width` / `output_height` as the base.

**Then**: [`preview_image_keypoints`](../mcp/tools.md#preview_image_keypoints) and
[`normalize_coordinates`](../mcp/tools.md#normalize_coordinates) for the parameters;
[`draw_keypoints`](../api/image.md#annotools.image.overlay.draw_keypoints) and
[`KeypointObject`](../api/image.md#annotools.image.overlay.KeypointObject) for the library contract.
Which points to ask for, how many correction rounds to allow, and how to catch a systematically
shifted skeleton are in
[`skills/localization-annotation-guide`](https://github.com/hoshiori-dev/annotools/tree/main/skills/localization-annotation-guide);
committing the accepted points is [`skills/sqlite-annotation-store`](https://github.com/hoshiori-dev/annotools/tree/main/skills/sqlite-annotation-store).
