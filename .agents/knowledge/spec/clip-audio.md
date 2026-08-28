# clip_audio

## Goal

Hand a model only the audio segment it needs, at the sample rate the caller chooses, without shipping
the whole file.

## Interface

Tool: `clip_audio` (MCP) / `annotools.audio.clip_audio` (library)

| Parameter | Type | Default | Constraints |
|---|---|---|---|
| `source` | str | — | local path or fsspec URL of an audio (or video) file |
| `start` | float \| null | null | seconds, ≥ 0 |
| `end` | float \| null | null | seconds, > `start` |
| `sample_rate` | int \| null | null | ≥ 1; resample when given, else keep the source rate |
| `save_to` | str \| null | null | also write the WAV to this path/URL |

Returns: one `audio/wav` block followed by one JSON text block: `source_duration`, `start`, `end`,
`duration`, `sample_rate`, `channels`, `format: "wav"`, `saved_to` when used.

## Behavior

1. Open the source with PyAV (`annotools[media]`; missing → `ImportError` naming the extra) through a
   streamed fsspec handle; a source without an audio stream, or undecodable content, raises `ValueError`
   naming it.
2. Seek to `start` (keyframe-safe), decode the first audio stream, drop samples before `start`, stop at
   `end` (or the end of the stream).
3. Resample to `sample_rate` when given (channel layout kept), then encode 16-bit PCM WAV in memory.
- Error: `start < 0`, `end ≤ start` (start defaults to 0), `sample_rate < 1` → `ValueError`; `start`
  beyond the source duration → `ValueError`.

## Acceptance criteria

1. `test_ac1_clip_bounds`: a 10 s synthetic tone clipped 2–5 s → WAV duration 3 s ± 0.05.
2. `test_ac2_resample`: `sample_rate=8000` → WAV header 8000 Hz; without it the source's 44100 Hz.
3. `test_ac3_invalid_range`: `start=5, end=5`, `start=-1`, `start=20` (beyond 10 s) → `ValueError`.
4. `test_ac4_and_ac5_tool`: `Client(mcp)` returns an `AudioContent` (`audio/wav`) then a JSON text
   block with `duration ≈ 3`, and `save_to` writes bytes identical to the returned audio.
5. `test_ac6_multichannel_kept`: a 6-channel source clips to a 6-channel WAV.
6. `test_ac7_errors_name_source`: a non-media file → `ValueError` naming it; `end=0` → `ValueError`.

## Out of scope

Compressed output formats; loudness normalization; channel mixing.

## References

issue #31; FastMCP `fastmcp.utilities.types.Audio`.
