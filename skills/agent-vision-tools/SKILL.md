---
name: agent-vision-tools
description: >-
  Builds the tools an execution agent uses to look at items and check its own annotations — on top
  of the annotools library for the Claude Agent SDK and the Codex SDK, confined to
  the project workspace. Use when wiring an SDK pipeline that must "see" images, video frames, or
  overlays, when an execution agent needs record/update tools, or when deciding how an agent is
  kept inside workspaces/<task>/. Not for the annotools MCP server itself (that serves coding
  agents) and not for prompt design.
compatibility: Python 3.12+, annotools installed from the repository; claude-agent-sdk or the Codex SDK.
---

# Agent Vision Tools

Execution agents never talk to the annotools MCP server; their developers build three small tool
families on the `annotools` library and register them with the SDK, all scoped to the workspace.

## Workflow

1. **Decide the tool set** from the task spec: `look_at_item` (preview with optional grid/crop) and
   `look_at_annotations` (overlay the agent's candidate boxes/points/polygons/mask) ship here. The
   store writers (`record_annotation`, `update_annotation`, `mark_reviewed`) are specified by the
   `sqlite-annotation-store` skill's tool contract and are implemented alongside these with the same
   SDK wiring. Captioning needs only `look_at_item` plus the writers.
2. **Implement on the library layer**: `annotools.io.load_image` → `annotools.image.preview.preview`
   → `annotools.image.grid.draw_grid` / `annotools.image.overlay.draw_bboxes` … →
   `annotools.image.preview.encode`. Return bytes; never call the MCP tools from the pipeline.
   Copy [assets/vision_tools.py](assets/vision_tools.py) as the SDK-independent core.
3. **Register with the SDK**:
   - Claude Agent SDK: [assets/claude_tools.py](assets/claude_tools.py) — `@tool` handlers return
     MCP content blocks (`{"type": "image", "data": <base64>, "mimeType": "image/jpeg"}` plus a text
     block with the metadata JSON); wrap them with `create_sdk_mcp_server`, pass `mcp_servers`,
     `allowed_tools=["mcp__vision__*"]`, `tools=[]` (no built-ins) and `cwd=<workspace>`.
   - Codex SDK: [assets/codex_tools.py](assets/codex_tools.py) — expose the same functions as a
     FastMCP server (stdio) and register it in the thread config (`mcp_servers`); start threads
     with `cwd=<workspace>` and `sandbox=Sandbox.workspace_write` (Python) or
     `startThread({ workingDirectory, sandboxMode })` (TypeScript). Read
     [references/sdk-notes.md](references/sdk-notes.md) when a parameter name is in doubt.
4. **Confine**: the workspace is the only path the tools accept — resolve every `item_uri` against
   `workspaces/<task>/` and refuse anything outside (see `_inside()` in the asset); disable file
   and shell built-ins; keep the DB path fixed in the tool closure, never a parameter.
5. **Budget**: pass `max_width`/`max_height` from `config/` (per-model sweet spot from
   `mllm-multimodal-input`); cap overlays per call; log `usage` per item.
   Done when: a dry run on 3 items shows the image inline in the agent transcript, the overlay call
   renders the agent's own boxes, and writes land in `dataset.db` with the run id.

## Gotchas

- Claude Agent SDK image blocks need raw base64 (no `data:` prefix) and an explicit `mimeType`;
  Python `@tool` forwards only `content` and `is_error` (no `structuredContent`) — put metadata in a
  text block.
- Codex threads default to the git repo check; when the workspace is not a repo pass
  `skipGitRepoCheck: true` (TS) or run inside the project repo with `cwd` set.
- Overlays are drawn from coordinates normalized to the **uncropped** source; when the agent looked
  at a crop, convert its answer through the preview metadata first (`localization-annotation-guide`).
- A preview tool that accepts arbitrary paths is a file-read primitive — the `_inside()` check is the
  security boundary, not the sandbox.
