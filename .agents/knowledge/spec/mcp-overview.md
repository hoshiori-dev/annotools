# MCP overview: shared conventions

## Goal

Every annotools MCP tool returns a compact preview an MLLM can read cheaply, plus machine-readable
metadata so an agent can map what it sees back to source coordinates. This document defines the
conventions and parameter groups every tool spec reuses; a tool spec only describes what it adds.

## Coordinates and colors

- All coordinates in parameters and metadata are normalized floats in `[0.0, 1.0]` relative to the
  **uncropped** source image (x → width, y → height). Pixel coordinates never cross the tool boundary.
- Colors are CSS/PIL color names (`blue`, `red`) or `#RRGGBB`; default `blue`.
- Defaults live in `annotools.config` and can be overridden with `ANNOTOOLS_<NAME>` environment
  variables at server start (e.g. `ANNOTOOLS_MAX_PREVIEW_WIDTH=1024`).

## `PreviewOptions` (every preview tool)

| Parameter | Type | Default | Constraints |
|---|---|---|---|
| `source` | str | — | local path or fsspec URL (`file://`, `s3://`, `gs://`, `http(s)://`, `memory://`) |
| `crop` | `[x_min, y_min, x_max, y_max]` \| null | null | normalized; `x_min < x_max`, `y_min < y_max`; zoom into a region |
| `target_pixels` | int \| null | null | ≥ 1; output area cap, combined with `max_*` (smallest wins) |
| `max_width` | int | 768 | ≥ 1 |
| `max_height` | int | 768 | ≥ 1 |
| `allow_upscale` | bool | false | when false the output never exceeds the (cropped) source size |
| `output_format` | `"jpeg"` \| `"png"` \| `"webp"` | `"jpeg"` | JPEG quality 90; alpha is flattened onto white for JPEG |
| `save_to` | str \| null | null | also write the encoded bytes to this path/URL |

Processing order: load (EXIF orientation applied) → crop → fit → overlays (tool-specific) → encode.

## `GridOptions` (tools that accept `grid`)

| Parameter | Type | Default | Constraints |
|---|---|---|---|
| `columns` | int | 10 | ≥ 1; `columns − 1` vertical lines |
| `rows` | int | 10 | ≥ 1 |
| `mode` | `"ratio"` \| `"fixed"` | `"ratio"` | `fixed` uses `column_width`/`row_width` in output pixels |
| `column_width` | int \| null | null | required when `mode="fixed"` |
| `row_width` | int \| null | null | required when `mode="fixed"` |
| `color` | `"white"` \| `"black"` \| `"invert"` | `"white"` | `invert` inverts the underlying pixels |
| `opacity` | float | 0.5 | `[0, 1]` |
| `line_width` | int | 1 | ≥ 1, output pixels |

## Object models

| Model | Fields |
|---|---|
| `BBoxObject` | `bbox: [x_min, y_min, x_max, y_max]`, `label: str \| null`, `color: str = "blue"` |
| `KeypointObject` | `point: [x, y]`, `label`, `color` |
| `PolygonObject` | `points: [x1, y1, x2, y2, …]` (even count, ≥ 6), `label`, `color` |

## Return shape

Every preview tool returns two content blocks in this order:

1. an image block (`image/jpeg`, `image/png`, or `image/webp`);
2. a text block containing **one JSON object** (no other text) with at least:

| Key | Meaning |
|---|---|
| `original_size` | `[width, height]` of the uncropped source after EXIF orientation |
| `crop` | the **applied** normalized box — the request rounded outward to whole source pixels — or the full frame `[0, 0, 1, 1]` |
| `output_size` | `[width, height]` of the returned image |
| `scale` | output pixels per source pixel (`output_width / cropped_source_width`) |
| `format` | the encoded format |
| `saved_to` | the `save_to` value when used, else absent |

Tools add keys (`grid`, `objects`, …) documented in their own spec. To map an output pixel `(px, py)`
back: `x = crop.x_min + px / output_width × (crop.x_max − crop.x_min)` and likewise for `y` — exact
because `crop` is the applied box and `scale = output_width / (crop width in source pixels)`.

## Sources and `save_to`

`source` is read through fsspec: local paths always work; `s3://`, `gs://`, `http(s)://` need the matching
backend, installed by the `annotools[remote]` extra (`s3fs`, `gcsfs`, `aiohttp`, `requests`). `save_to`
writes wherever fsspec can write (parent directories are created for local paths); a failed write raises
`OSError` naming the target and the tool returns no image. The server does not restrict paths — deploy
it with the filesystem access you intend agents to have.

## Errors

Invalid parameters raise `ValueError` naming the parameter (surfaced as an MCP tool error). A missing
source raises `FileNotFoundError`; any other read failure (permissions, unknown protocol, missing backend
or credentials) raises `OSError`; undecodable, truncated, or corrupt content raises `ValueError`; a failed
`save_to` raises `OSError`. Each message names the URI. Tools never return partial images.

## References

`.agents/knowledge/mllm-token-budget.md`; FastMCP
media helper classes (`fastmcp.utilities.types.Image`).
