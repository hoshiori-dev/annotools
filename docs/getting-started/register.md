---
icon: lucide/plug
---

# Register the server

annotools speaks MCP over stdio, and over HTTP with `--http`. Any MCP client can start it; the three
below are the ones this repository is tested against.

Pick the preview size for the model behind the agent — it is the one setting worth changing up front.
384 px (the default) keeps a Gemini image at one 258-token unit, while Claude and GPT bill by area and
read 768 px comfortably. Every setting is listed in [As an MCP server](../usage/mcp-server.md).

=== "Claude Code"

    `.mcp.json` in the project root:

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

    Restart Claude Code; `/mcp` then lists `annotools` and its 13 tools.

=== "Codex"

    `.codex/config.toml` in the project root:

    ```toml
    [mcp_servers.annotools]
    command = "uv"
    args = ["run", "annotools"]
    env = { ANNOTOOLS_MAX_WIDTH = "768", ANNOTOOLS_MAX_HEIGHT = "768" }
    ```

=== "OpenCode"

    `opencode.json` in the project root:

    ```json
    {
      "$schema": "https://opencode.ai/config.json",
      "mcp": {
        "annotools": {
          "type": "local",
          "command": ["uv", "run", "annotools"],
          "enabled": true,
          "environment": { "ANNOTOOLS_MAX_WIDTH": "768", "ANNOTOOLS_MAX_HEIGHT": "768" }
        }
      }
    }
    ```

## Without uv

`uv run annotools` resolves the project environment on every start. If annotools is already installed
in an environment, point the client at the executable instead:

```json
{ "command": "annotools", "args": [], "env": { "ANNOTOOLS_MAX_WIDTH": "768" } }
```

The container works the same way — `docker` as the command, with the dataset directory mounted at
`/data`:

```json
{
  "command": "docker",
  "args": ["run", "--rm", "-i", "-v", "/path/to/data:/data", "ghcr.io/hoshiori-dev/annotools"]
}
```

## Over HTTP

For debugging, or for a client that speaks HTTP rather than stdio:

```bash
uv run annotools --http --host 127.0.0.1 --port 8000
```

## Check it works

```bash
uv run annotools --version
```

Then ask the agent to call `preview_image` on any image path. It answers with a downscaled image plus
a one-line JSON metadata block naming `original_size`, the applied `crop`, `output_size` and `scale` —
the numbers that map anything the model says back to the full-resolution source.
