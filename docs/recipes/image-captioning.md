---
icon: lucide/message-square-text
---

# Image captioning

Describe or tag an image by sending the model one downscaled preview instead of the full-resolution
file.

=== "Library"

    ```python
    from annotools import encode, load_image, preview

    view = preview(load_image("photo.jpg"), max_width=768, max_height=768)
    jpeg = encode(view.image, "jpeg")  # the bytes to attach to the model call

    print(view.metadata["output_size"], view.metadata["scale"])
    ```

    On a 1600x1200 source this prints `[768, 576] 0.48`. `load_image` applies EXIF orientation, so
    the view matches what a person would see; the same `PreviewResult` can be re-encoded as PNG or
    WebP without re-reading the file.

=== "MCP"

    `preview_image`:

    ```json
    {
      "source": "photo.jpg",
      "max_width": 768,
      "max_height": 768
    }
    ```

    Returns the JPEG followed by one metadata object: `original_size`, the applied `crop`
    (`[0, 0, 1, 1]` here), `output_size`, `output_width` / `output_height`, `scale`, and `format`.
    For small text or one detail, call it again with `crop` set to a normalized region such as
    `[0.55, 0.1, 0.85, 0.4]`, which spends the same token budget on a quarter of the frame.

Captioning is linear — one preview per image, one model call, one write — so the only real cost lever
is the preview size. Pick it for the model behind the agent: 384 px keeps a Gemini image at one
258-token unit, while Claude and GPT bill by area and read 768-1024 px comfortably.

**Then**: [`preview_image`](../mcp/tools.md#preview_image) for every parameter and the crop rules,
[`preview`](../api/image.md#annotools.image.preview.preview) and
[`encode`](../api/image.md#annotools.image.preview.encode) for the library contract, and
[`skills/task-image-captioning`](https://github.com/hoshiori-dev/annotools/tree/main/skills/task-image-captioning)
for the requirement checklist, prompt templates, and pipeline skeleton. Complete pipelines:
[`examples/image-captioning-claude`](https://github.com/hoshiori-dev/annotools/tree/main/examples/image-captioning-claude)
and [`examples/image-captioning-codex`](https://github.com/hoshiori-dev/annotools/tree/main/examples/image-captioning-codex).
