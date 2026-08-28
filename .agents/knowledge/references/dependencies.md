# Dependency Reference

Runtime components the library and server build on: version pinned in `uv.lock`, the documentation used,
the verification date, and where the project uses it. Verify against this file before using an API from
memory; if a fact is missing, read the docs (the `fastmcp-docs` MCP server is registered for FastMCP)
and add it here.

| Component | Version (uv.lock, 2026-08-27) | Docs | Used in |
|---|---|---|---|
| FastMCP | 3.4.7 | https://gofastmcp.com (servers/tools, media helpers; `fastmcp-docs` MCP) | `mcp/server.py`, `mcp/*` |
| MCP SDK (`mcp`) | 1.29.1 | https://github.com/modelcontextprotocol/python-sdk | content types in tests (`ImageContent`, `TextContent`) |
| pydantic | 2.13.4 | https://docs.pydantic.dev | parameter models, `Annotated[..., Field]` aliases in `mcp/common.py` |
| pydantic-settings | 2.15.0 | https://docs.pydantic.dev/latest/concepts/pydantic_settings/ | `config.py` (`Settings`), `mcp/cli.py` (`CliSettingsSource`) |
| Pillow | 12.3.0 | https://pillow.readthedocs.io | `io.py`, `image/*` |
| numpy | 2.5.2 | https://numpy.org/doc | `image/grid.py`, `image/segmentation.py`, `audio.py` |
| fsspec | 2026.7.0 | https://filesystem-spec.readthedocs.io | `io.py` (`open_bytes`, `write_bytes`) |
| PyAV (`av`, extra `media`) | 18.1.0 | https://pyav.org/docs | `video.py`, `audio.py` |
| s3fs / gcsfs / aiohttp / requests (extra `remote`) | 2026.7.0 / 2026.8.0 / 3.14.3 / 2.34.2 | fsspec implementations | remote URLs in `io.py` |

## FastMCP 3.x

- Tools return media through `fastmcp.utilities.types.Image(data=bytes, format="jpeg")` and `Audio`;
  a list such as `[Image, str]` becomes image + text content blocks. A tool whose return type is a list
  of content blocks must be declared `@mcp.tool(output_schema=None)`, otherwise FastMCP raises
  "outputSchema defined but no structured output". Pydantic-model returns get structured output
  automatically (`rotated_bbox_to_polygon`).
- `FastMCP(name, instructions=...)` lives in `annotools/mcp/app.py` (imports no tool module); tool modules
  register by importing them, which `mcp/server.py` does at module level (composition root).
- Enumerate registered tools with `await mcp.list_tools()` (2026-08-28, 3.4.7): there is no public
  `_tool_manager` attribute on the server object.
- Tools returning a pydantic model give structured output; tests read it via
  `result.structured_content["key"]` (`result.data` is a generated `Root` object, not a dict).
- Tests use the in-memory transport: `async with Client(mcp) as client: await client.call_tool(name,
  args, raise_on_error=False)`; `result.content` holds the blocks, `result.is_error` the error flag.
- `mcp.run()` is stdio; `mcp.run(transport="http", host=, port=)` serves Streamable HTTP.
- Parameter descriptions come from `Annotated[type, Field(description=...)]`; constraints (`ge`, `le`)
  surface in the input schema (`test_preview_options_schema_matches_tool_aliases` guards drift).

## pydantic-settings 2.15

- `class Settings(BaseSettings)` with `model_config = SettingsConfigDict(env_prefix="ANNOTOOLS_",
  env_ignore_empty=True)`: env overrides defaults, empty env values are ignored, init kwargs beat env.
- CLI on an existing argparse parser (verified 2026-08-27):
  `source = CliSettingsSource(Settings, root_parser=parser, cli_parse_args=False, cli_kebab_case=True)`
  adds `--max-width` style flags; after `ns = parser.parse_args(argv)`,
  `Settings(_cli_settings_source=source(parsed_args=ns))` resolves CLI > env > default.
  `cli_show_env_vars=True` prints the env var name in `--help`.
- Import cost ≈ 0.2 s; the server import (≈ 1.5 s) stays deferred in `cli.main` so `--help` is fast.
- pydantic 2.13 omits `default_factory` values from the JSON schema, so a model field whose default comes from
  `get_settings()` at call time advertises no default; the MCP layer therefore keeps import-time snapshots for
  flat tool parameters, and nested `GridOptions` fields show `null` (verified 2026-08-28).

## PyAV

- `av.open(file_like)` over an `fsspec.open(uri, "rb")` handle; video: `container.streams.video[0]`,
  `stream.time_base`, `container.seek(int(t / stream.time_base), stream=stream, backward=True,
  any_frame=False)`, `frame.to_image()` (PIL); audio: `av.AudioResampler(format="s16", layout=...,
  rate=...)` then the stdlib `wave` module writes the WAV bytes (no PyAV encoder needed).
- Wheels bundle FFmpeg; the devcontainer has no system `ffmpeg`, which is fine.

## fsspec

- `fsspec.open(url, "rb")` handles `file://`, plain paths, `memory://`, and — with the `remote` extra —
  `s3://`, `gs://`, `http(s)://`. Errors are re-raised naming the URI (`io.py`).

## Pillow / numpy

- Apply `ImageOps.exif_transpose` before measuring `original_size`.
- Resize ID masks with `Image.NEAREST` only; convert `I;16` modes through numpy, not `convert("L")`.
- Previews resize with `LANCZOS` when downscaling and `BICUBIC` when upscaling; JPEG quality 90 default.
