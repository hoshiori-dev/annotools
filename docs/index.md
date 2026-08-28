---
icon: lucide/rocket
---

# annotools

Let agents see and annotate multimodal data within a token budget. annotools downscales and
crop-zooms images, video frames and audio, draws grid guide lines and BBox / keypoint / polygon /
segmentation overlays, and keeps every coordinate in one convention — normalized 0.0–1.0 relative to
the uncropped source.

It serves two audiences, both first-class:

<div class="grid cards" markdown>

-   :material-power-plug: **An MCP server for coding agents**

    ---

    Register `annotools` with Claude Code, Codex or OpenCode and the agent can look at a dataset the
    way you would — a downscaled preview, a zoom into one region, a grid to anchor positions — without
    blowing its context on full-resolution images.

    [:octicons-arrow-right-24: Tool reference](mcp/tools.md)

-   :material-package-variant: **A library for agent developers**

    ---

    The same previews, overlays and coordinate conversions as plain Python functions, so a pipeline
    built on the Claude Agent SDK or the Codex SDK can give its own execution agent eyes. Importing
    `annotools` never loads `fastmcp`.

    [:octicons-arrow-right-24: API reference](api/index.md)

</div>

## Install

```bash
uv add "annotools @ git+https://github.com/hoshiori-dev/annotools"
```

Add the `media` extra for video and audio, or run the container
(`ghcr.io/hoshiori-dev/annotools`) — see [Install](getting-started/install.md). Then
[register the server](getting-started/register.md) with Claude Code, Codex or OpenCode and set the
preview size for the model behind the agent: 384 px keeps a Gemini image at one 258-token unit, while
Claude and GPT bill by area and read 768 px comfortably.

## Use the library

```python
from annotools import BBoxObject, draw_bboxes, encode, load_image, normalize_coordinates, preview

result = preview(load_image("photo.jpg"), max_width=768, max_height=768)
boxes = normalize_coordinates([[120, 80, 300, 260]], result.metadata["output_width"], result.metadata["output_height"])
overlay = draw_bboxes(result, [BBoxObject(bbox=boxes[0], label="cat")])
image_bytes = encode(overlay.image, "jpeg")
```

## More

- [As an MCP server](usage/mcp-server.md) and [As a library](usage/library.md) — settings, coordinates, and the shape of a call.
- [API reference](api/index.md) — every public function, generated from its docstring.
- [MCP tool reference](mcp/tools.md) — parameters, return shape and specification of all 13 tools.
- [Architecture](architecture.md) — layers and recorded decisions.
- [Recipes](recipes/index.md) — one page per task (captioning, detection, keypoints, polygons,
  segmentation, video, audio), each as library code and as the MCP call.
- [Cookbook](cookbook/index.md) — how an agent-run annotation project gets from an interview to an
  exported dataset, one page per step.
- Skills — the annotation methodology as installable agent skills: `npx skills add hoshiori-dev/annotools`.
- [Examples](https://github.com/hoshiori-dev/annotools/tree/main/examples) — four complete pipelines
  (image captioning and object detection, on the Claude Agent SDK and the Codex SDK).
