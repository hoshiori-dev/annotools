---
icon: lucide/book-open
---

# API reference

`annotools` is a library as much as it is an MCP server. Everything listed in `annotools.__all__` is
public API: it carries a complete docstring, appears on these pages, and stays stable within a minor
version. Module paths (`annotools.image.preview`, `annotools.geometry`, …) remain importable, so both
of these work:

```python
from annotools import preview, draw_bboxes, normalize_coordinates
from annotools.image.preview import preview  # the same function
```

Anything not listed here is internal: underscore names, underscore modules (`annotools._media`,
`annotools.image._draw`), and the whole `annotools.mcp` package, which is the MCP server rather than
library API. Importing `annotools` never loads `fastmcp`.

| Module | What it covers |
|---|---|
| [`annotools.config`](config.md) | `Settings` and the process-wide defaults every other call falls back to |
| [`annotools.io`](io.md) | Reading and writing media through fsspec (local paths and remote URLs alike) |
| [`annotools.color`](color.md) | Color parsing and stable text-to-color hashing for labels and mask IDs |
| [`annotools.geometry`](geometry.md) | Normalized coordinates, size fitting, rotated boxes, per-model coordinate conversion |
| [`annotools.image`](image.md) | Previews, grids, bbox / keypoint / polygon overlays, segmentation masks |
| [`annotools.video`](video.md) | Frame sampling (`annotools[media]`) |
| [`annotools.audio`](audio.md) | Clipping and resampling to WAV (`annotools[media]`) |
