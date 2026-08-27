---
name: spec-driven-feature
description: >-
  Implements an annotools feature end to end in the project's order — issue, spec in docs/spec/, failing
  tests, implementation, docs — for any new or changed MCP tool, library function, CLI option, or example
  output contract. Use when asked to "add a tool", "implement", "change the parameters of", "support
  <format>", or when starting work on a Task issue. Not for harness-only or documentation-only changes.
---

# Spec-Driven Feature

## Workflow

1. **Issue.** Confirm an open issue exists (create one via `github-project-workflow` if not). Its
   `Acceptance criteria` section is the contract; if it is vague, sharpen it in the issue before coding.
   Done when: every criterion names a command, test, or observable output.
2. **Spec.** Write or update `docs/spec/<feature>.md` following `.agents/knowledge/spec-format.md`
   (Goal, Interface, Behavior, Acceptance criteria, Out of scope, References); start from
   [assets/spec-template.md](assets/spec-template.md). Define shared parameter groups
   (`PreviewOptions`, `GridOptions`) once in `docs/spec/mcp-overview.md` (create it with the first tool
   spec) and reference them from every tool spec.
   Defaults must match `annotools.config`. Copy the acceptance criteria into the issue if they changed.
3. **Tests first.** One test per acceptance criterion, named `test_ac<n>_<slug>`, in
   `tests/test_<module>.py`. Use generated fixtures (`PIL.Image.new`, numpy arrays) — no committed
   binaries. MCP tools: test the library function directly and the tool through
   `async with Client(mcp) as client: await client.call_tool(...)`. Run `just test` and confirm the new
   tests fail for the expected reason.
4. **Implement.** Library function in `src/annotools/<area>/` (PIL/numpy in, PIL/bytes out, no
   `fastmcp` import, `ValueError` with a specific message on contract violations), then the MCP wrapper
   in `src/annotools/tools/` (pydantic model, `@mcp.tool`, returns `[Image(data=..., format=...), json
   metadata string]`). Register the tool module in `annotools.server`.
5. **Docs.** Update the tool table in `README.md` and `README.zh.md` together (`just readme-check`) and
   any affected knowledge file.
6. **Verify.** `just check` green; call the tool once through the real server
   (`uv run python scripts/smoke_stdio.py "$(uv run which annotools)"` lists tools; a manual call from
   Claude Code / Codex / OpenCode confirms the image renders). Then hand off to
   `github-project-workflow` to finish the PR.

## Gotchas

- Coordinates arrive normalized to the **uncropped** source; convert after cropping using the crop box,
  not the output size.
- `fastmcp.utilities.types.Image` converts to an MCP content block only when returned directly or inside
  a list, never nested in a dict.
- Return metadata as one JSON line (original size, output size, scale, crop, grid step) so agents can map
  coordinates back; tests assert on it.
- `ruff format` also formats Python blocks in Markdown — spec examples must be formatted.
- Video/audio code imports `av` lazily and raises a clear `ImportError` naming `annotools[media]`.
