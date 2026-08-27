# SDK notes (verified 2026-08-27)

## Claude Agent SDK (Python `claude-agent-sdk`, TypeScript `@anthropic-ai/claude-agent-sdk`)
- `@tool(name, description, schema)` handler returns `{"content": [...], "is_error"?: bool}`; content
  blocks: `text`, `image` (`data` base64 without prefix, `mimeType` required), `resource`,
  `resource_link`; Python drops `audio` blocks. `create_sdk_mcp_server(name, version, tools)`.
- `ClaudeAgentOptions(cwd, tools=[], mcp_servers={...}, allowed_tools=["mcp__<server>__*"],
  disallowed_tools, permission_mode="dontAsk"|"acceptEdits"|"plan"|"default"|"bypassPermissions"|"auto")`.
  `tools=[]` removes every built-in; `allowed_tools` pre-approves; a bare name in `disallowed_tools`
  removes a built-in from context.
- Tool names: `mcp__<server_name>__<tool_name>`. Tool search is on by default (schemas load on demand).
- Source: https://code.claude.com/docs/en/agent-sdk/custom-tools

## Codex SDK
- TypeScript `@openai/codex-sdk`: `new Codex({ config?, configOverrides?, env?, baseUrl? })`,
  `codex.startThread({ workingDirectory?, skipGitRepoCheck? })`, `thread.run(prompt, { outputSchema? })`,
  `thread.runStreamed(...)`. Config keys flatten to Codex `config.toml` dotted paths (e.g.
  `sandbox_workspace_write.network_access`), which is also how `mcp_servers` are declared.
- Python `openai-codex`: `Codex()`, `codex.thread_start(model=, sandbox=Sandbox.read_only |
  workspace_write | full_access, cwd=, config=, approval_mode=, base_instructions=)`,
  `thread.run(prompt, output_schema=, effort=)`; `TurnResult` carries the final response, items, usage.
- MCP servers are declared through config (`mcp_servers.<name>.command/args`), the same shape as
  `.codex/config.toml`; there is no in-process tool decorator, hence the FastMCP server in the asset.
- Sources: https://github.com/openai/codex/tree/main/sdk (typescript/README.md, python/docs/api-reference.md)
