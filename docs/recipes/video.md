---
icon: lucide/film
---

# Video

Turn a clip into a bounded number of gridded still frames, which is the only video input Claude and
GPT accept in the vision path.

=== "Library"

    ```python
    from annotools import GridOptions, draw_grid, encode, preview, sample_frames

    frames, info = sample_frames("clip.mp4", fps=1.0, end=6.0, max_frames=8)
    shots = []
    for timestamp, frame in frames:
        view = preview(frame, max_width=384, max_height=384)
        view.image = draw_grid(view.image, GridOptions(columns=10, rows=10)).image
        shots.append((timestamp, encode(view.image, "jpeg")))

    print(info["duration"], info["thinned"], [t for t, _ in shots])
    ```

    On a 6-second clip this prints `6.0 False [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]`. `sample_frames` picks
    the first decoded frame at or after each target time, then thins evenly to `max_frames` (keeping
    the first and last) and reports `thinned: True` when it had to — a long clip cannot quietly blow
    the budget. It needs PyAV: `uv add "annotools[media]"`.

=== "MCP"

    `preview_video_grid` (or `preview_video` without the grid):

    ```json
    {
      "source": "clip.mp4",
      "fps": 1.0,
      "end": 6.0,
      "max_frames": 8,
      "columns": 10,
      "rows": 10,
      "max_width": 384,
      "max_height": 384
    }
    ```

    Returns the frames in time order, then one metadata object: `frames`, `timestamps` (seconds,
    rounded to milliseconds), `duration`, `requested_fps`, `thinned`, the `grid` layout, and the
    first frame's size, `crop` and `scale`. `save_to` is a directory here, not a file — frames land
    in it as `frame_<index>_<time>.<ext>`. Coordinates read off a frame are normalized against that
    first-frame geometry, the same as for a still image.

**Then**: [`preview_video`](../mcp/tools.md#preview_video) and
[`preview_video_grid`](../mcp/tools.md#preview_video_grid) for the parameters, and
[`sample_frames`](../api/video.md#annotools.video.sample_frames) for the library contract. Frame
budget per model — Gemini samples video natively at 1 fps and 258 tokens per frame, Claude and GPT
need the frames as images — is in
[`skills/mllm-multimodal-input`](https://github.com/hoshiori-dev/annotools/tree/main/skills/mllm-multimodal-input).
