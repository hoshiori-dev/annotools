# Architecture

annotools is a small, layered Python project: a pure library that turns media plus annotations into
compact preview images, wrapped by a FastMCP server so coding agents can call it as MCP tools, and
accompanied by publishable skills and example agent pipelines that use the same library. `AGENTS.md`
points here for structure; this file explains how the parts fit.

## Overview

```text
 skills/ (methodology + scaffolding)      examples/ (Claude Agent SDK / Codex SDK pipelines)
 ────────────────────────────────────────────────────────────────────────────────────────────
 src/annotools/server.py + tools/         MCP layer: pydantic parameter models, @mcp.tool wrappers,
                                          Image/Audio content blocks + one-line JSON metadata
 ────────────────────────────────────────────────────────────────────────────────────────────
 src/annotools/{io,geometry,color,        library layer: pure functions, PIL/numpy in, PIL/bytes out,
               image/,video/,audio/}      no fastmcp import; reused by execution agents' own tools
```

Two kinds of agents use the project:

- **Coding agents** (Claude Code, Codex, OpenCode) develop annotation pipelines. They call the MCP tools to
  look at data cheaply and follow the skills to design SQLite-backed projects.
- **Execution agents** (built with the Claude Agent SDK or Codex SDK inside a project) run the pipelines.
  They never see the MCP server or source; their developers build them tools on top of the library layer,
  scoped to a workspace directory.

## Tech Stack

- Python ≥ 3.12, managed with uv (`uv_build` backend); ruff for lint/format, ty for types, pytest.
- FastMCP 3 for the MCP server (stdio default, `--http` optional).
- Pillow + numpy for rendering, fsspec for local/remote file access, pydantic for parameter models.
- PyAV (`av`) behind the optional `media` extra for video frame extraction and audio clipping.
- Container image on GHCR (`ghcr.io/hoshiori-dev/annotools`); PyPI publishing is prepared but disabled.

## Layout

Modules marked *(planned)* are tracked by issue #1 and its milestones; design drafts are not committed.

```text
src/annotools/
  cli.py            argparse entrypoint: `annotools [--http] [--host] [--port]`
  server.py         FastMCP("annotools") instance; tool modules register onto it
  config.py         defaults (768×768 max preview, border 2, point 3, grid 10×10, opacity 0.5); ANNOTOOLS_* env
  io.py             open_bytes(uri) via fsspec; decode to PIL
  geometry.py       normalized↔pixel coordinates, crop math, rotated box → 4 corners, is_rectangle
  color.py          text → stable color hash, color parsing, inversion
  image/            preview (crop+resize), grid, overlay (bbox/keypoint/polygon), segmentation
  video.py          frame sampling by fps → image pipeline (PyAV, media extra)
  audio.py          (planned) clip + resample → WAV
  tools/            MCP wrappers: image_tools, color_tools, geometry_tools, video_tools, audio_tools (planned)
tests/              unit tests with generated fixtures; container tests behind the `container` marker
.agents/knowledge/spec/          one specification per MCP tool (goal, parameters, return, acceptance criteria)
skills/ examples/   (planned) publishable skills; independent example projects (each with CONTEXT.md)
```

## Key Flows

1. **Preview request** — tool parameters (pydantic) → `io.open_bytes` → PIL image → optional crop →
   resize to fit `max_width`/`max_height`/`target_pixels` (downscale only unless `allow_upscale`) →
   optional grid → overlays drawn in output pixel space from normalized coordinates → encode (JPEG q90
   default) → returned as `[Image, metadata JSON]`. Metadata carries original size, output size, scale,
   applied crop, and grid step so agents can convert coordinates back.
2. **Segmentation preview** — single-channel ID mask (uint8/uint16, 0 = background) resized to the
   source with nearest-neighbour, colored by `color_from_text(str(id))`, blended at `alpha`; `legend`
   mode appends a legend strip before the final resize so the output still fits the limits.
3. **Release** — GitHub release `v<version>` → CI workflow (verify) → wheel + image build → smoke tests
   → GHCR push; see `.github/workflows/release.yml`.

## Decisions

- Normalized coordinates everywhere (frontier MLLMs localize better with size-independent coordinates);
  revisit only if a target training format demands absolute pixels at the tool boundary.
- 768 px long side by default (owner decision): a conservative ceiling that keeps every frontier model's
  per-image cost bounded while preserving enough detail for localization. It is *not* a single Gemini
  tile — Gemini bills ≤ 384 px images as one unit and tiles larger ones; OpenAI tiles at 512 px. Per-model
  sweet spots and the verified formulas live in `.agents/knowledge/mllm-token-budget.md`; tools accept
  `max_width`/`max_height` per call so a pipeline can pick a cheaper size.
- Library layer independent of FastMCP so execution agents can reuse it without an MCP client.
- SQLite is the assumed annotation store in skills and examples; nothing in the library depends on it.
- Rotated boxes are exchanged as DOTA-style 8 numbers (4 corners); `theta` defaults to degrees.
- Separate, complete example projects per SDK rather than shared scaffolding — closer to real usage.
