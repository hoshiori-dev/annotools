---
icon: lucide/plug
---

# Register the server

annotools speaks MCP over stdio, and over HTTP with `--http`. Any MCP client can start it; the three
below are the ones this repository itself is configured for.

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

    Restart Claude Code and approve the project-scoped server when prompted; `/mcp` then lists
    `annotools` and its tools.

=== "Codex"

    `.codex/config.toml` in the project root:

    ```toml
    [mcp_servers.annotools]
    command = "uv"
    args = ["run", "annotools"]
    env = { ANNOTOOLS_MAX_WIDTH = "768", ANNOTOOLS_MAX_HEIGHT = "768" }
    ```

    Codex reads a project's `.codex/` configuration only for a project you have trusted.

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
{
  "command": "annotools",
  "args": [],
  "env": { "ANNOTOOLS_MAX_WIDTH": "768", "ANNOTOOLS_MAX_HEIGHT": "768" }
}
```

That fragment is Claude Code's shape; use the `command` / `args` / `env` spelling of whichever client
you configured above.

The container works the same way — `docker` as the command, with the dataset directory mounted at
`/data`:

```json
{
  "command": "docker",
  "args": [
    "run", "--rm", "-i",
    "-v", "/path/to/data:/data",
    "-e", "ANNOTOOLS_MAX_WIDTH=768",
    "-e", "ANNOTOOLS_MAX_HEIGHT=768",
    "ghcr.io/hoshiori-dev/annotools:0.1.0-rc1"
  ]
}
```

## Over HTTP

For debugging, or for a client that speaks HTTP rather than stdio:

```bash
uv run annotools --http --host 127.0.0.1 --port 8000
```

The endpoint is `http://127.0.0.1:8000/mcp`; the bare root returns 404.

From the container, bind to all interfaces inside it and publish the port:

```bash
docker run --rm -p 8000:8000 -v "$PWD:/data" ghcr.io/hoshiori-dev/annotools:0.1.0-rc1 \
  --http --host 0.0.0.0 --port 8000
```

## Check it works

```bash
uv run annotools --version
```

Then ask the agent to call `preview_image` on any image path. It answers with a downscaled image plus
a one-line JSON metadata block naming `original_size`, the applied `crop`, `output_size` and `scale` —
the numbers that map anything the model says back to the full-resolution source.
