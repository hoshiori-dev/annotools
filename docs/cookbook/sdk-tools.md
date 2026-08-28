# Give the execution agent tools

The agent that labels item 700 is not a coding agent and does not talk to the annotools MCP server.
It runs inside your pipeline, once per item, with a small fixed tool set built on the
[annotools library](../api/index.md) and registered with an agent SDK. The MCP server serves the
developer; the library serves the pipeline.

Two vision tools cover every task family:

- `look_at_item(uri, crop=None, grid=None)` — the preview the model localizes on.
- `look_at_annotations(uri, bboxes=…, keypoints=…, polygons=…)` — the agent's own candidates drawn
  back onto the same view, which is what makes the [correction loop](localization-loop.md) possible.

Alongside them go the three store writers — `record_annotation`, `update_annotation`,
`mark_reviewed` — from [step 2](store.md). Captioning needs `look_at_item` and the writers only.

The core is short enough to read: load, preview at the size from `config/`, draw the grid, encode.

```python
from annotools import GridOptions, draw_grid, encode, load_image, preview


def look_at_item(uri: str, max_width: int = 768, max_height: int = 768) -> tuple[bytes, dict]:
    """Return the bytes the execution agent sees and the metadata its answer refers to."""
    result = preview(load_image(uri), max_width=max_width, max_height=max_height)
    gridded = draw_grid(result.image, GridOptions(columns=10, rows=10))
    return encode(gridded.image, "jpeg"), {**result.metadata, **gridded.metadata}
```

The metadata is not decoration: `output_width`, `output_height`, and the applied `crop` are what
turn the model's answer into a stored coordinate. Return it with every image.
[`assets/vision_tools.py`](https://github.com/hoshiori-dev/annotools/blob/main/skills/agent-vision-tools/assets/vision_tools.py)
is this core with the overlay tool and the workspace check added.

## Wiring, per SDK

The Claude Agent SDK takes in-process tools: a `@tool` handler returns MCP content blocks, wrapped
by `create_sdk_mcp_server` and passed as `mcp_servers`. The image block needs raw base64 with no
`data:` prefix and an explicit `mimeType`, and the Python `@tool` forwards only `content` and
`is_error` — no `structuredContent` — so the metadata travels as a text block next to the image.
Pass `tools=[]` to remove every built-in and `allowed_tools=["mcp__vision__*"]` to pre-approve
yours.

The Codex SDK has no in-process decorator: the same functions become a FastMCP stdio server declared
in the thread config, and threads start with `cwd` set to the workspace and a sandbox mode. Two
things reliably cost an afternoon. Codex threads check for a git repository, so a workspace outside
one needs `skipGitRepoCheck` in TypeScript, or a `cwd` inside the project repository — the Python
`thread_start()` has no such parameter, which is why both Codex examples run from inside the repo.
And `ApprovalMode.deny_all`, the natural choice for an unattended run, rejects MCP tool calls too —
every call fails with `user rejected MCP tool call` — so the server entry needs
`"default_tools_approval_mode": "approve"`.

[`assets/claude_tools.py`](https://github.com/hoshiori-dev/annotools/blob/main/skills/agent-vision-tools/assets/claude_tools.py)
and [`assets/codex_tools.py`](https://github.com/hoshiori-dev/annotools/blob/main/skills/agent-vision-tools/assets/codex_tools.py)
are both wirings of the same core; the parameter names are recorded, dated, in
[`references/sdk-notes.md`](https://github.com/hoshiori-dev/annotools/blob/main/skills/agent-vision-tools/references/sdk-notes.md).

## Confinement is the tool's job

A preview tool that accepts an arbitrary path is a file-read primitive. Every `uri` resolves against
`workspaces/<task>/` and anything landing outside is refused; the database path lives in the tool
closure and is never a parameter; file and shell built-ins stay off. The sandbox is a second line,
not the boundary.

The last piece is budget: preview sizes come from `config/`, not from the library defaults (which
are Gemini's 384 px), overlays per call are capped, and `usage` is logged per item so the
[trial](trial-and-confirm.md) has something to read.

A tool set is done when a dry run on three items shows the image inline in the transcript, the
overlay call renders the agent's own boxes, and the writes land in `dataset.db` under the run id.
All four [example projects](https://github.com/hoshiori-dev/annotools/tree/main/examples) implement
exactly this — `src/*/tools.py` in each — two on each SDK.

Next: [trial and confirm](trial-and-confirm.md).

Source: [`skills/agent-vision-tools`](https://github.com/hoshiori-dev/annotools/tree/main/skills/agent-vision-tools)
