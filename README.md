# annotools

[中文](README.zh.md)

MCP server and Python library that help agents look at multimodal data — images, video, audio — within an
MLLM token budget, plus skills and examples for building agentic annotation pipelines on SQLite.

## Why

Feeding full-resolution media to a multimodal model is expensive and imprecise. annotools gives coding
agents cheap, purpose-built views: downscaled previews, crop-zoom, grid guide lines, and overlays of
BBoxes, keypoints, polygons, and segmentation masks so an agent can check its own annotations before
committing them. The same functions are available as a library for the execution agents you build with
the Claude Agent SDK or the Codex SDK.

## Status

Under construction — milestone P0 (harness). The MCP server starts but registers no tools yet. Follow
the [tracking issue](https://github.com/hoshiori-dev/annotools/issues/1).

## Install

```bash
uv add annotools            # library + MCP server (PyPI publishing is not enabled yet; install from git)
uv add "annotools[media]"   # adds PyAV for video and audio tools
```

Container: `docker run --rm -i ghcr.io/hoshiori-dev/annotools` (stdio) or add `--http --host 0.0.0.0`
with `-p 8000:8000`.

## Use as an MCP server

Register `uv run annotools` (stdio) with your agent framework. This repository's own configuration shows
the three shapes: `.mcp.json` (Claude Code), `.codex/config.toml` (Codex), `opencode.json` (OpenCode).
`annotools --http --port 8000` serves Streamable HTTP for shared or remote use.

## Tools (planned)

| Tool | Purpose |
|---|---|
| `preview_image` | crop + downscale to fit 768×768 (configurable) |
| `preview_image_grid` | preview with a semi-transparent 10×10 grid |
| `preview_image_bboxes` / `_keypoints` / `_polygons` | overlays from normalized coordinates, optional labels |
| `preview_image_segmentation` | ID-mask overlay with labels or a legend |
| `color_from_text` | stable color from any text |
| `rotated_bbox_to_polygon` | (cx, cy, w, h, θ) → DOTA 8-number corners |
| `preview_video` / `preview_video_grid` | frame sampling at N fps → previews |
| `clip_audio` | clip and resample audio |

Specifications live in `docs/spec/`.

## Skills and examples

`skills/` will hold installable skills (`npx skills add hoshiori-dev/annotools`) for interviewing users
about an annotation task, SQLite annotation schemas, per-model multimodal input strategies, localization
guidance, and task scaffolds. `examples/` will hold complete example projects (image captioning, object
detection) for both SDKs, each with its recorded usage.

## Development

```bash
uv sync --all-extras
just check          # lint, format, types, taxonomy, README sync, unit tests
just docker-build && just test-container
```

See `CONTRIBUTING.md`; agents start from `AGENTS.md`.

## License

Apache-2.0
