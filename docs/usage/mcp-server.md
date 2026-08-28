---
icon: lucide/server
---

# As an MCP server

The `annotools` command is an MCP server with 13 tools. An agent that has it can look at a dataset the
way a person would — a downscaled preview, a zoom into one region, a grid to anchor positions, an
overlay of the boxes it just proposed — without spending its context on full-resolution images.

Everything a tool returns is an image plus one line of JSON metadata. The metadata is what makes the
view reversible: `original_size`, the applied `crop`, `output_size` and `scale` together map any
coordinate the model produces back to the uncropped source.

For the parameters of each tool, see the [tool reference](../mcp/tools.md).

## Settings

Defaults are resolved once at start-up, in this order: command-line flag, then `ANNOTOOLS_<FIELD>`
environment variable, then the built-in value. Empty environment values are ignored; an invalid value
fails at start-up naming the field. The resolved values are the defaults an agent sees in every tool
schema, so setting them well is how you tune cost without touching prompts.

| Setting | Flag / variable | Default | Meaning |
|---|---|---|---|
| `max_width`, `max_height` | `--max-width` / `ANNOTOOLS_MAX_WIDTH` | 384, 384 | preview size limits in pixels |
| `target_pixels` | `--target-pixels` | null | cap on output area, combined with the size limits |
| `grid_columns`, `grid_rows` | `--grid-columns` | 10, 10 | cells in the guide grid |
| `grid_mode` | `--grid-mode` | `ratio` | `ratio` = equal cells; `fixed` = cells of a given pixel size |
| `grid_column_width`, `grid_row_width` | `--grid-column-width` | null | cell size in output pixels, required by `fixed` |
| `grid_opacity`, `grid_line_width` | `--grid-opacity` | 0.5, 1 | grid line rendering |
| `line_width`, `point_diameter` | `--line-width` | 2, 3 | overlay outline width and dot diameter |
| `color` | `--color` | `blue` | default overlay color |
| `output_format`, `jpeg_quality` | `--output-format` | `jpeg`, 90 | encoding of the returned image |

`uv run annotools --help` prints the same list with each variable name.

## Choosing a preview size

The preview limit is a token budget in disguise. Set it for the model behind the agent:

| Model family | Suggested limit | Why |
|---|---|---|
| Gemini | 384 | an image with both sides ≤ 384 px costs one 258-token unit; above that it is tiled |
| Claude | 768–1024 | one token per 28×28 px patch, so cost grows with area; 1024 px stays inside the standard tier |
| GPT / Codex | 768–1024 | 32×32 px patches times a per-model factor, likewise area-proportional |

The per-model numbers, with sources and verification dates, live in
[`.agents/knowledge/references/mllm-models.md`](https://github.com/hoshiori-dev/annotools/blob/main/.agents/knowledge/references/mllm-models.md)
and in the `mllm-multimodal-input` skill.

## Coordinates

Every coordinate crossing the tool boundary — in parameters and in metadata — is normalized to
0.0–1.0 relative to the **uncropped** source, x against width and y against height. Pixels never cross
that boundary.

Models are worst at answering in that convention, so ask each model in its own: Claude and Qwen2.5-VL
in pixels of the image they saw, Gemini and Qwen3-VL in a 0–1000 space (Gemini writes `y, x`), GPT in
0–999. Then convert with the `normalize_coordinates` tool, passing the preview's `output_width` /
`output_height` (or 1000 / 999) as the base and the applied `crop` when the model looked at a zoom.

## Transports

Stdio is the default and is what MCP clients expect. HTTP is available for debugging:

```bash
uv run annotools --http --port 8000
```

## Confining what the server can read

The server reads any path or URL it is given, through fsspec. It is a file-read primitive: run it with
the working directory (or the container mount) scoped to the dataset you want the agent to see.
