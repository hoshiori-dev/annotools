# Agent SDK Reference

APIs the example projects and the `agent-vision-tools` skill rely on. Versions are those pinned in the
examples' `uv.lock` (2026-08-27). The published skill copy is
`skills/agent-vision-tools/references/sdk-notes.md`, derived from this file.

## Claude Agent SDK — `claude-agent-sdk` 0.2.145 (Python), `@anthropic-ai/claude-agent-sdk` (TS)

- Docs: https://code.claude.com/docs/en/agent-sdk (custom tools: `/custom-tools`).
- In-process tools: `@tool(name, description, schema)`; handler returns `{"content": [...],
  "is_error"?: bool}`; content blocks `text`, `image` (`data` base64 without prefix, `mimeType`
  required), `resource`, `resource_link`; Python drops `audio` blocks.
  `create_sdk_mcp_server(name, version, tools)`.
- `ClaudeAgentOptions(cwd, tools=[], mcp_servers={...}, allowed_tools=["mcp__<server>__*"],
  disallowed_tools, permission_mode="dontAsk", system_prompt, effort, max_turns, max_budget_usd)`;
  `tools=[]` removes every built-in; tool names are `mcp__<server>__<tool>`.
- `query(prompt, options)` yields messages; `ResultMessage.usage` / `total_cost_usd` for the record.

## Codex SDK — `openai-codex` 0.147.0 (Python), `@openai/codex-sdk` (TS)

- Docs: https://github.com/openai/codex/tree/main/sdk (`python/docs/api-reference.md`,
  `typescript/README.md`).
- Python: `Codex()`, `codex.thread_start(model=, sandbox=Sandbox.read_only | workspace_write |
  full_access, approval_mode=ApprovalMode.deny_all, cwd=, config={"mcp_servers": {...}},
  base_instructions=)`; `thread.run(prompt, output_schema=, effort=)` → `TurnResult` with the final
  response, items, and `usage` (`usage.total` aggregates input/cached/output tokens).
- No in-process tool decorator: tools are served as an MCP stdio server declared under
  `config["mcp_servers"][name] = {"command": ..., "args": [...]}` (same shape as `.codex/config.toml`).
- TS: `new Codex({config?, env?})`, `codex.startThread({workingDirectory, skipGitRepoCheck})`,
  `thread.run(prompt, {outputSchema?})`, `thread.runStreamed(...)`.

## Shared practice

- Confine the execution agent to `workspaces/<task>/` (SDK `cwd` + tool-side path checks); it never
  sees ground-truth annotations.
- Static system prompt first, per-item content last, so provider prompt caches hit
  (`references/mllm-models.md` for minimums).
