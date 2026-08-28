# preview_video / preview_video_grid

<!-- --8<-- [start:user] -->

## Goal

Show a video as a bounded sequence of small frames — sampled at a low frame rate, capped in count, and
each rendered through the image preview pipeline — instead of loading the whole video into a model.

## Interface

Tools: `preview_video`, `preview_video_grid` (MCP) / `annotools.video.sample_frames` (library)

Parameters: `PreviewOptions` (applied to every frame) plus

| Parameter | Type | Default | Constraints |
|---|---|---|---|
| `fps` | float | 1.0 | > 0; target sampling rate in frames per second |
| `start` | float \| null | null | seconds, ≥ 0 |
| `end` | float \| null | null | seconds, > `start` |
| `max_frames` | int | 32 | ≥ 1; hard cap on returned frames |

`preview_video_grid` adds the flat `GridOptions` parameters of `preview_image_grid`.

Returns: N image blocks (in time order) followed by one JSON text block with the base keys of the
first frame plus `frames: N`, `timestamps: [seconds…]`, `duration: seconds`, `requested_fps`,
`thinned: bool`, and `grid` for the grid variant.

## Behavior

1. Open the source with PyAV (`annotools[media]`) through a streamed fsspec handle (local and remote
   alike); a missing dependency raises `ImportError` naming the extra; undecodable content raises
   `ValueError` naming the source.
2. Decode the first video stream from `start` (keyframe seek, then skip) to `end` (or the end of the
   stream); select the first decoded frame whose time reaches each target `start + k / fps`.
3. If more than `max_frames` frames were selected, keep `max_frames` of them evenly spaced by index
   (always including the first) and set `thinned` to true.
4. Render each frame with the image preview (crop, limits, upscale rule) and, for the grid variant,
   the grid; encode with `output_format`. `save_to` is treated as a directory: frames are written as
   `frame_<index>_<timestamp>.<ext>` inside it.
- Error: `fps ≤ 0`, `start < 0`, `end ≤ start` (start defaults to 0), `max_frames < 1` → `ValueError`;
  no video stream, or no frame inside `[start, end)` → `ValueError` naming the source; unreadable source
  → as `preview_image`.

<!-- --8<-- [end:user] -->

## Acceptance criteria

1. `test_ac1_default_fps`: 5 s synthetic video at 10 fps → 5 frames at t ≈ 0, 1, 2, 3, 4 s (±0.1).
2. `test_ac2_start_end`: `start=1, end=3` → 2 frames at ≈ 1 and 2 s.
3. `test_ac3_max_frames_thinning`: `fps=10`, `max_frames=8` on 5 s → 8 frames, first at 0 s, evenly
   spaced; `thinned` true.
4. `test_ac4_frames_previewed`: 1920×1080 frames → each ≤ 384 px long side (384×216); grid variant metadata has
   `grid`.
5. `test_ac5_missing_extra`: with `av` unimportable the library raises `ImportError` mentioning
   `annotools[media]`.
6. `test_ac6_tool`: `Client(mcp)` returns N image blocks followed by one JSON text block whose
   `frames == N` (both tools).
7. `test_ac7_save_to_directory`: `save_to` writes `frame_0000_0.000.<ext>` … into the directory.
8. `test_ac8_errors_name_source`: an audio-only file, a non-media file, and an empty range each raise
   `ValueError` naming the source.

<!-- --8<-- [start:user2] -->

## Out of scope

Audio; scene detection; overlays on frames (use the image tools on saved frames).

<!-- --8<-- [end:user2] -->

## References

issue #30; `.agents/knowledge/mllm-token-budget.md`.
