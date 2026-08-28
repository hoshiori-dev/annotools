<p align="center">
  <img src="docs/assets/logo.svg" width="88" alt="">
</p>

<h1 align="center">annotools</h1>

<p align="center">
  Let agents see and annotate multimodal data within a token budget.
</p>

<p align="center">
  <a href="https://github.com/hoshiori-dev/annotools/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/hoshiori-dev/annotools/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Coverage" src="https://img.shields.io/badge/coverage-%3E%3D95%25-brightgreen">
  <img alt="Python" src="https://img.shields.io/badge/python-3.12%2B-blue">
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-Apache--2.0-blue"></a>
  <a href="https://hoshiori-dev.github.io/annotools/"><img alt="Docs" src="https://img.shields.io/badge/docs-site-blue"></a>
</p>

<p align="center">
  <a href="https://hoshiori-dev.github.io/annotools/">Documentation</a> ·
  <a href="README.zh.md">中文</a>
</p>

<p align="center">
  <img src="docs/assets/pipeline.svg" width="700" alt="Source image, downscaled preview, grid overlay, box overlay, coordinates normalized to the source">
</p>

Feeding full-resolution media to a multimodal model is expensive and imprecise. annotools gives an
agent purpose-built views instead — downscaled previews, crop-zoom, grid guide lines, and overlays of
boxes, keypoints, polygons and segmentation masks so it can check its own annotations before
committing them. Every coordinate stays in one convention: normalized 0.0–1.0 relative to the
uncropped source.

## Two ways to use it

| 🔌 An MCP server for coding agents | 📦 A library for agent developers |
|---|---|
| 13 tools for Claude Code, Codex and OpenCode | The same previews, overlays and conversions as functions |
| The agent looks at a dataset for a fraction of the context | Give your own execution agent eyes, no MCP client needed |
| Preview size is a setting, so cost is tuned per model | `import annotools` never loads `fastmcp` |
| [→ Tool reference](https://hoshiori-dev.github.io/annotools/mcp/tools/) | [→ API reference](https://hoshiori-dev.github.io/annotools/api/) |

## Quick start

```bash
uv add "annotools[media] @ git+https://github.com/hoshiori-dev/annotools"
```

Pre-1.0: install from git until PyPI publishing is enabled. The `media` extra adds PyAV, which the
video and audio tools need; drop it for images only.

### As an MCP server

Register the `annotools` command over stdio. For Claude Code, `.mcp.json`:

```json
{
  "mcpServers": {
    "annotools": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "annotools"],
      "env": { "ANNOTOOLS_MAX_WIDTH": "768", "ANNOTOOLS_MAX_HEIGHT": "768" }
    }
  }
}
```

Set the preview size for the model behind the agent: 384 px (the default) keeps a Gemini image at one
258-token unit, while Claude and GPT bill by area and read 768 px comfortably. Codex and OpenCode
shapes, every setting, and the HTTP transport are in
[Register the server](https://hoshiori-dev.github.io/annotools/getting-started/register/).

### As a library

```python
from annotools import BBoxObject, draw_bboxes, encode, load_image, normalize_coordinates, preview

result = preview(load_image("photo.jpg"), max_width=768, max_height=768)
boxes = normalize_coordinates(
    [[240, 130, 470, 505]],
    result.metadata["output_width"],
    result.metadata["output_height"],
)
overlay = draw_bboxes(result, [BBoxObject(bbox=boxes[0], label="cat")])
jpeg = encode(overlay.image, "jpeg")
```

## Tools

| Tool | What it does |
|---|---|
| `preview_image` | crop + downscale to fit the size limits |
| `preview_image_grid` | preview with a semi-transparent grid to anchor positions |
| `preview_image_bboxes` | box overlays from normalized coordinates, optional labels |
| `preview_image_keypoints` | keypoint overlays from normalized coordinates, optional labels |
| `preview_image_polygons` | polygon overlays with numbered vertices |
| `preview_image_segmentation` | ID-mask overlay with per-region labels or a legend |
| `preview_video` | frame sampling at N fps → one preview per frame |
| `preview_video_grid` | frame sampling at N fps → a grid on every frame |
| `clip_audio` | cut and resample audio to WAV |
| `color_from_text` | stable color from any text |
| `rotated_bbox_to_polygon` | (cx, cy, w, h, θ) → DOTA 8-number corners |
| `normalize_coordinates` | a model's frame (pixels, or 0–1000) → normalized 0–1 |
| `denormalize_coordinates` | normalized 0–1 → a model's frame |

Parameters, return shapes and specifications:
[tool reference](https://hoshiori-dev.github.io/annotools/mcp/tools/).

## Documentation

- [Get started](https://hoshiori-dev.github.io/annotools/getting-started/install/) — install, extras, container, MCP registration.
- [Usage](https://hoshiori-dev.github.io/annotools/usage/mcp-server/) — settings, coordinate conventions, the shape of a library call.
- [API reference](https://hoshiori-dev.github.io/annotools/api/) — every public function, generated from its docstring.
- [Architecture](https://hoshiori-dev.github.io/annotools/architecture/) — layers and recorded decisions.
- [`skills/`](skills/) — the annotation methodology, installable into your agent: `npx skills add hoshiori-dev/annotools`.
- [`examples/`](examples/) — four complete pipelines: captioning and detection, on the Claude Agent SDK and the Codex SDK.

## Development

```bash
uv sync --all-extras
just check
just docker-build && just test-container
```

`just check` runs lint, format, types, taxonomy, README sync, the public-API docstring check, the
generated-reference drift check, a strict docs build, and the tests behind a 95% coverage gate. See
[`CONTRIBUTING.md`](CONTRIBUTING.md); agents start from [`AGENTS.md`](AGENTS.md).

## License

Apache-2.0
