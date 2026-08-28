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

Under construction — all milestones implemented; the example projects await their first live runs
(usage records). All planned MCP tools are available. Follow
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

Preview defaults are settings: flags override `ANNOTOOLS_*` environment variables, which override the
built-in values (`annotools --help` lists them; the pre-0.1 `ANNOTOOLS_MAX_PREVIEW_WIDTH` names are gone). The 384 px default is Gemini's single-unit size; for
Claude, GPT, or Qwen start the server with a larger limit, e.g. `uv run annotools --max-width 768
--max-height 768` or `ANNOTOOLS_MAX_WIDTH=768 ANNOTOOLS_MAX_HEIGHT=768` in the MCP registration
(see `.mcp.json`). Other settings: `--target-pixels`, `--grid-columns`, `--grid-rows`, `--grid-mode`,
`--grid-column-width`, `--grid-row-width`, `--line-width`, `--point-diameter`, `--color`,
`--output-format`, `--jpeg-quality`.

## Tools (planned)

| Tool | Purpose |
|---|---|
| `preview_image` | crop + downscale to fit 384×384 (configurable) |
| `preview_image_grid` | preview with a semi-transparent 10×10 grid |
| `preview_image_bboxes` | bounding-box overlays from normalized coordinates, optional labels |
| `preview_image_keypoints` | keypoint overlays from normalized coordinates, optional labels |
| `preview_image_polygons` | polygon overlays from normalized coordinates, optional labels |
| `preview_image_segmentation` | ID-mask overlay with labels or a legend |
| `color_from_text` | stable color from any text |
| `rotated_bbox_to_polygon` | (cx, cy, w, h, θ) → DOTA 8-number corners |
| `normalize_coordinates` | a model's frame (pixels of the preview, or 0–1000) → normalized 0–1 |
| `denormalize_coordinates` | normalized 0–1 → a model's frame (pixels of the preview, or 0–1000) |
| `preview_video` | frame sampling at N fps → one preview per frame |
| `preview_video_grid` | frame sampling at N fps → a grid on every frame |
| `clip_audio` | clip and resample audio |

Specifications live in `.agents/knowledge/spec/` (shared conventions: `.agents/knowledge/spec/mcp-overview.md`);
the generated tool reference is at `docs/mcp/tools.md`.

## Skills and examples

`skills/` holds installable skills (`npx skills add hoshiori-dev/annotools`). All seven ship:
`annotation-project-interview` (design-tree interview + workspace scaffold), `sqlite-annotation-store`
(schema, tool contract, exports), `mllm-multimodal-input` (per-model token cost, coordinate conventions,
cache layout), `localization-annotation-guide` (the grid → propose → verify → correct → commit loop),
`agent-vision-tools` (execution-agent tools on the library for the Claude Agent SDK and Codex SDK),
`task-image-captioning`, and `task-object-detection` (task scaffolds with prompts and pipeline skeletons). `examples/` holds four complete example projects — image captioning and object detection, each for the
Claude Agent SDK and the Codex SDK — with their own `CONTEXT.md`, spec, tests, and a usage record to fill
after the first run.

## Development

```bash
uv sync --all-extras
just check          # lint, format, types, taxonomy, README sync, unit tests
just docker-build && just test-container
```

See `CONTRIBUTING.md`; agents start from `AGENTS.md`.

## License

Apache-2.0
