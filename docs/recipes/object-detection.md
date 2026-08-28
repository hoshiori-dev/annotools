---
icon: lucide/square-dashed
---

# Object detection

Ask a model for axis-aligned boxes on a gridded preview, convert its answer into normalized
coordinates, then render the boxes back so it can correct them before you store anything.

=== "Library"

    ```python
    from annotools import (
        BBoxObject,
        GridOptions,
        draw_bboxes,
        draw_grid,
        encode,
        load_image,
        normalize_coordinates,
        preview,
    )

    source = load_image("photo.jpg")
    view = preview(source, max_width=768, max_height=768)
    view.image = draw_grid(view.image, GridOptions(columns=10, rows=10)).image
    gridded = encode(view.image, "jpeg")  # ask the model for boxes on this view

    width, height = view.metadata["output_size"]
    answer = [[144, 72, 432, 360]]  # the model's pixels of the view it saw
    boxes = normalize_coordinates(answer, width, height, crop=view.metadata["crop"])

    check = draw_bboxes(preview(source, max_width=768, max_height=768), [BBoxObject(bbox=boxes[0], label="cat")])
    ```

    `boxes` is `[[0.1875, 0.125, 0.5625, 0.625]]` — normalized to the uncropped source, which is
    what the store keeps. `draw_grid` returns a new result, but only its image is taken: `view` keeps
    the `crop` and `scale` that `draw_bboxes` maps the boxes through.

=== "MCP"

    `preview_image_grid`, then `normalize_coordinates` on the answer, then
    `preview_image_bboxes` to show the model its own boxes:

    ```json
    { "source": "photo.jpg", "columns": 10, "rows": 10, "max_width": 768, "max_height": 768 }
    ```

    ```json
    { "coordinates": [[144, 72, 432, 360]], "base_width": 768, "base_height": 576 }
    ```

    ```json
    {
      "source": "photo.jpg",
      "objects": [{ "bbox": [0.1875, 0.125, 0.5625, 0.625], "label": "cat" }],
      "grid": { "columns": 10, "rows": 10 },
      "max_width": 768,
      "max_height": 768
    }
    ```

    The grid call adds `grid` (`columns`, `rows`, `step_x` / `step_y`, `cell_width` / `cell_height`)
    to the usual metadata; `normalize_coordinates` answers `{"coordinates": [[...]]}`; the box call
    adds `objects`, the number drawn. Repeat propose → verify → correct by index for a bounded number
    of rounds, then commit.

**Then**: [`preview_image_grid`](../mcp/tools.md#preview_image_grid),
[`preview_image_bboxes`](../mcp/tools.md#preview_image_bboxes) and
[`normalize_coordinates`](../mcp/tools.md#normalize_coordinates) for the parameters;
[`draw_bboxes`](../api/image.md#annotools.image.overlay.draw_bboxes) and
[`normalize_coordinates`](../api/geometry.md#annotools.geometry.normalize_coordinates) for the
library contract. The loop itself — class definitions, prompts, round limits, quality checks — is in
[`skills/task-object-detection`](https://github.com/hoshiori-dev/annotools/tree/main/skills/task-object-detection)
and [`skills/localization-annotation-guide`](https://github.com/hoshiori-dev/annotools/tree/main/skills/localization-annotation-guide);
complete pipelines in
[`examples/object-detection-claude`](https://github.com/hoshiori-dev/annotools/tree/main/examples/object-detection-claude)
and [`examples/object-detection-codex`](https://github.com/hoshiori-dev/annotools/tree/main/examples/object-detection-codex).
