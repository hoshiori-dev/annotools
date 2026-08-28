---
icon: lucide/chef-hat
---

# Recipes

One page per annotation task, each showing the same work twice: as library calls inside a Python
pipeline, and as the MCP tool call a coding agent makes. Parameters are not repeated here — the
[tool reference](../mcp/tools.md) carries the full tables and the specification behind each tool.

| Recipe | Produces | Main tool |
|---|---|---|
| [Image captioning](image-captioning.md) | text per image | `preview_image` |
| [Object detection](object-detection.md) | axis-aligned boxes | `preview_image_bboxes` |
| [Keypoints](keypoints.md) | named points | `preview_image_keypoints` |
| [Polygons](polygons.md) | outlines and oriented boxes | `preview_image_polygons` |
| [Segmentation](segmentation.md) | ID masks | `preview_image_segmentation` |
| [Video](video.md) | frames per clip | `preview_video_grid` |
| [Audio](audio.md) | WAV segments | `clip_audio` |

## What every recipe assumes

Coordinates are normalized 0-1 relative to the **uncropped** source, x-first. A model does not answer
in that convention: Claude and Qwen2.5-VL answer in pixels of the image they saw, Gemini and Qwen3-VL
in a 0-1000 space (Gemini y-first), GPT in 0-999. Every localization recipe therefore passes the
answer through
[`normalize_coordinates`](../api/geometry.md#annotools.geometry.normalize_coordinates) with the frame
the model used, plus the preview's applied `crop` when it looked at a zoom, before anything is drawn
or stored.

The library snippets import from `annotools` (`uv add "annotools @ git+https://github.com/hoshiori-dev/annotools"`);
the video and audio recipes additionally need the `media` extra for PyAV. The MCP snippets are the
arguments object for a registered `annotools` server — see [Get started](../index.md) for registering
it and for choosing `max_width` / `max_height` for the model behind the agent.

The sample values below come from a 1600x1200 `photo.jpg` previewed at 768x576.
