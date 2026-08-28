# Architecture

annotools is a small, layered Python project: a pure library that turns media plus annotations into
compact preview images, wrapped by a FastMCP server so coding agents can call it as MCP tools, and
accompanied by publishable skills and example agent pipelines that use the same library. `AGENTS.md`
points here for structure; this file explains how the parts fit.

## Overview

```text
 skills/ (methodology + scaffolding)      examples/ (Claude Agent SDK / Codex SDK pipelines)
 ────────────────────────────────────────────────────────────────────────────────────────────
 src/annotools/mcp/                       MCP layer: FastMCP app, CLI, pydantic parameter models,
                                          @mcp.tool wrappers,
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

Modules marked *(planned)* are tracked by the current cycle's tracking issue (see `AGENTS.md`, "Current
cycle") and its milestones; design drafts are not committed.

```text
src/annotools/
  __init__.py       package version (public facade planned, #84)
  __main__.py       `python -m annotools` → mcp.cli.main()
  config.py         `Settings` (pydantic-settings): 384×384 max preview, grid 10×10, line 2, point 3; flags > ANNOTOOLS_* env
  io.py             open_bytes(uri) via fsspec; decode to PIL
  geometry.py       normalized↔pixel coordinates, crop math, rotated box → 4 corners, is_rectangle
  color.py          text → stable color hash, color parsing, inversion
  image/            preview (crop+resize), grid, overlay (bbox/keypoint/polygon), segmentation; _draw.py internal helpers
  video.py          frame sampling by fps → image pipeline (PyAV, media extra)
  audio.py          clip + resample → WAV (PyAV, media extra)
  _media.py         internal: PyAV import guard + fsspec-backed container opening shared by video/audio
  mcp/              MCP layer (the only package importing fastmcp):
    app.py            FastMCP("annotools") instance + instructions; imports no tool module (no import cycle)
    server.py         composition root: imports app.mcp and every tool module so their @mcp.tool decorators run
    cli.py            `annotools` command: flags/env → config.configure() → deferred server import → mcp.run()
    common.py         Annotated[..., Field] parameter aliases, PreviewOptions, render_preview, finish, apply_grid
    image/video/audio/color/geometry.py   the 13 @mcp.tool wrappers, one module per library area
tests/              unit tests with generated fixtures; container tests behind the `container` marker
.agents/knowledge/  spec/ one specification per MCP tool (goal, parameters, return, acceptance criteria)
skills/ examples/   publishable skills; independent example projects (each with CONTEXT.md)
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

## Knowledge Layers

1. `.agents/knowledge/references/` — external facts (vendor token rules, coordinate conventions,
   dependency APIs, SDK APIs) with a verification date and URL per entry. Nothing here is a decision.
2. `.agents/knowledge/*.md` and this file's Decisions — project decisions that cite reference entries
   rather than raw URLs.
3. `skills/` — published derivatives for users; their `references/` files are trimmed copies of layer 1
   and are refreshed when layer 1 changes.

## Decisions

- Everything that imports `fastmcp` lives in the `annotools.mcp` package; `import annotools` never loads it
  (#82). Inside the package `mcp/app.py` holds the FastMCP instance and imports no tool module, `mcp/server.py`
  is the composition root, and tool modules never import `mcp.server`, so there is no import cycle (#69).
- Normalized coordinates everywhere (frontier MLLMs localize better with size-independent coordinates);
  revisit only if a target training format demands absolute pixels at the tool boundary.
- 384 px preview limit by default (owner decision, 2026-08-27): the largest size Gemini bills as a
  single 258-token unit (`references/mllm-models.md`). Claude, GPT patch models, and Qwen bill by area
  and read 768–1024 px previews well, so a deployment picks its size for the model it serves through
  `annotools --max-width/--max-height` or `ANNOTOOLS_MAX_WIDTH/HEIGHT`; every preview tool also accepts
  `max_width`/`max_height` per call. Recommended sizes per model: `skills/mllm-multimodal-input`.
- Library layer independent of FastMCP so execution agents can reuse it without an MCP client.
- SQLite is the assumed annotation store in skills and examples; nothing in the library depends on it.
- Rotated boxes are exchanged as DOTA-style 8 numbers (4 corners); `theta` defaults to degrees.
- Segmentation masks are single-channel ID images (uint8/uint16 PNG/TIFF; 0 = background; `MASK_MODES`
  in `image/segmentation.py`); any other mode is an error rather than a guess.
- Separate, complete example projects per SDK rather than shared scaffolding — closer to real usage.
- The public library API is exactly `annotools.__all__` (re-exported from each module's `__all__`); it gets
  full docstrings and appears in the API reference. Module paths (`annotools.image.preview`, ...) stay
  importable, underscore modules and everything outside `__all__` are internal, and `annotools.mcp` is not
  part of the library API (#84).
