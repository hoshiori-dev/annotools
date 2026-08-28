---
icon: lucide/blend
---

# Segmentation

Review an instance, panoptic, or semantic ID mask by blending it over the image, so a model can judge
regions it can actually see instead of a wall of pixel values.

=== "Library"

    ```python
    from annotools import load_image, load_mask, overlay_mask, preview

    view = preview(load_image("photo.jpg"), max_width=768, max_height=768)
    overlay = overlay_mask(
        view,
        load_mask("mask.png"),
        annotation="legend",
        id_names={1: "balloon", 2: "window"},
        alpha=0.5,
        max_width=768,
        max_height=768,  # the legend strip is appended, then the composite is re-fitted
    )

    print(overlay.metadata["ids"], overlay.metadata["image_size"])
    ```

    This prints `2 [768, 576]`. `load_mask` reads a single-channel ID image (`L`, `P`, `I`, `I;16`)
    where 0 is background; the mask is resized to the source with nearest neighbour, then follows the
    preview's crop and scale, so a mask at a different resolution than the photo still lines up. Pass
    the size limits explicitly in `legend` mode: the strip is appended below the image and the whole
    composite is re-fitted, otherwise to the 384 px default.

=== "MCP"

    `preview_image_segmentation`:

    ```json
    {
      "source": "photo.jpg",
      "mask_source": "mask.png",
      "annotation": "legend",
      "id_names": { "1": "balloon", "2": "window" },
      "alpha": 0.5,
      "max_width": 768,
      "max_height": 768
    }
    ```

    Returns the blended image plus metadata with `ids` (visible IDs) and, in legend mode, `legend`
    (`[{"id": 1, "name": "balloon", "color": "#20df83"}, ...]`) and `image_size`, the area above the
    strip that the inverse mapping applies to. `id_names` keys are strings in JSON. With
    `annotation: "label"` the ID is drawn at each region centre and no strip is added; colors come
    from `color_from_text(str(id))` either way, so an instance keeps its color across previews.

**Then**: [`preview_image_segmentation`](../mcp/tools.md#preview_image_segmentation) and
[`color_from_text`](../mcp/tools.md#color_from_text) for the parameters;
[`load_mask`](../api/image.md#annotools.image.segmentation.load_mask),
[`overlay_mask`](../api/image.md#annotools.image.segmentation.overlay_mask) and
[`color_from_text`](../api/color.md#annotools.color.color_from_text) for the library contract. Never
store the mask itself in the annotation database — store the file pointer. The review loop and its
quality controls are in
[`skills/localization-annotation-guide`](https://github.com/hoshiori-dev/annotools/tree/main/skills/localization-annotation-guide).
