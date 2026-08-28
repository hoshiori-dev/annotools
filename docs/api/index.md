---
icon: lucide/book-open
---

# API reference

`annotools` is a library as much as it is an MCP server. `annotools.__all__` is the public API: every
name in it carries a complete docstring, appears on these pages (except `__version__`, the package
version string), and stays stable within a minor version. Module paths (`annotools.image.preview`, `annotools.geometry`, …) remain importable, so both
of these work:

```python
from annotools import preview, draw_bboxes, normalize_coordinates
from annotools.image.preview import preview  # the same function
```

Anything outside `__all__` is internal and does not appear here: underscore names, underscore modules
(`annotools._media`, `annotools.image._draw`), cross-module helpers that keep a plain name for
readability, and the whole `annotools.mcp` package, which is the MCP server rather than library API.
Importing `annotools` never loads `fastmcp`.

| Module | What it covers |
|---|---|
| [`annotools.config`](config.md) | `Settings` and the process-wide defaults every other call falls back to |
| [`annotools.io`](io.md) | Reading and writing media through fsspec (local paths and remote URLs alike) |
| [`annotools.color`](color.md) | Color parsing and stable text-to-color hashing for labels and mask IDs |
| [`annotools.geometry`](geometry.md) | Normalized coordinates, size fitting, rotated boxes, per-model coordinate conversion |
| [`annotools.image`](image.md) | Previews, grids, bbox / keypoint / polygon overlays, segmentation masks |
| [`annotools.video`](video.md) | Frame sampling (`annotools[media]`) |
| [`annotools.audio`](audio.md) | Clipping and resampling to WAV (`annotools[media]`) |
