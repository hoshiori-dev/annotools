---
icon: lucide/package
---

# As a library

The MCP server is one consumer of annotools; your own agent can be another. Everything the tools do is
a plain function, so a pipeline built on the Claude Agent SDK or the Codex SDK can give its execution
agent the same eyes without running an MCP server at all. Importing `annotools` loads neither
`fastmcp` nor the `annotools.mcp` package.

`annotools.__all__` is the public API; the [API reference](../api/index.md) documents every name in it.

## The shape of a call

Preview first, overlay second, encode last. The preview carries the metadata everything else needs.

```python
from annotools import BBoxObject, draw_bboxes, encode, load_image, preview

image = load_image("photo.jpg")
result = preview(image, max_width=768, max_height=768)
overlay = draw_bboxes(result, [BBoxObject(bbox=(0.31, 0.44, 0.62, 0.78), label="cat")])
jpeg = encode(overlay.image, "jpeg")
```

`result.metadata` holds `original_size`, the applied `crop`, `output_size` and `scale`; `overlay`
adds `objects`. Boxes are in source coordinates, so the same call draws them correctly on a full view
and on a zoomed crop.

## Zooming without losing the frame

```python
zoom = preview(image, crop=(0.5, 0.5, 1.0, 1.0), max_width=768, max_height=768)
zoom.metadata["crop"]  # the crop actually applied, rounded outward to whole source pixels
```

Pass that `crop` to `normalize_coordinates` and a model's answer about the zoom lands in the full
image.

## Converting a model's answer

```python
from annotools import normalize_coordinates

# Claude answered in pixels of the 768-px preview it saw.
boxes = normalize_coordinates(
    [[240, 130, 470, 505]],
    zoom.metadata["output_width"],
    zoom.metadata["output_height"],
    crop=zoom.metadata["crop"],
)

# Gemini answered [ymin, xmin, ymax, xmax] in a 0-1000 space.
boxes = normalize_coordinates([[130, 240, 505, 470]], 1000, 1000, axis_order="yx")
```

[`denormalize_coordinates`](../api/geometry.md) is the inverse: use it to show a model its own stored
annotations in the frame it reasons in.

## Defaults

Every size, width and color parameter falls back to [`annotools.Settings`](../api/config.md) when you
pass `None`, resolved at call time:

```python
from annotools import Settings, configure

configure(Settings(max_width=1024, max_height=1024, color="red"))
preview(image)  # now 1024 px, overlays default to red
```

Because resolution happens per call, `configure()` affects everything that runs after it. The MCP
layer is the exception: it snapshots the settings when the server starts so its tool schemas can
advertise concrete numbers.

## Video and audio

Both need `annotools[media]` (PyAV). Frames come back as PIL images, ready for the same preview
pipeline:

```python
from annotools import clip_audio, preview, sample_frames

frames, meta = sample_frames("clip.mp4", fps=1, end=10, max_frames=8)
previews = [preview(frame, max_width=768, max_height=768) for _, frame in frames]

wav, audio_meta = clip_audio("talk.wav", start=30, end=45, sample_rate=16000)
```

## Building agent tools on top

The [`agent-vision-tools`](https://github.com/hoshiori-dev/annotools/tree/main/skills/agent-vision-tools)
skill packages this into the tools an execution agent actually needs: `look_at_item` and
`look_at_annotations` to see, writer tools to record, and the workspace confinement that keeps the
agent inside its dataset. The four
[example projects](https://github.com/hoshiori-dev/annotools/tree/main/examples) are complete working
versions of it.
