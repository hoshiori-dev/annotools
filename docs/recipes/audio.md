---
icon: lucide/audio-lines
---

# Audio

Cut the stretch of audio a model actually needs and hand it over as 16-bit WAV at the rate that model
expects.

=== "Library"

    ```python
    from annotools import clip_audio, write_bytes

    wav, info = clip_audio("talk.wav", start=2.0, end=8.0, sample_rate=16000)
    write_bytes("clips/talk_002_008.wav", wav)

    print(info["duration"], info["sample_rate"], info["channels"])
    ```

    This prints `6.0 16000 1`. The source can be a video file — `clip_audio` reads its first audio
    stream — and `end` is exclusive and clamped to the source duration, while a `start` beyond it is
    an error rather than an empty clip. `write_bytes` creates parent directories for local paths.
    Resampling is optional but usually worth it in the same call: most speech models want 16 kHz, and
    sending 44.1 kHz spends tokens on nothing. Needs PyAV: `uv add "annotools[media]"`.

=== "MCP"

    `clip_audio`:

    ```json
    {
      "source": "talk.wav",
      "start": 2.0,
      "end": 8.0,
      "sample_rate": 16000,
      "save_to": "clips/talk_002_008.wav"
    }
    ```

    Returns a WAV audio block followed by one metadata object: `source_duration`, `start`, `end`,
    `duration`, `sample_rate`, `channels`, `format`, and `saved_to` when `save_to` was given. It is
    the only tool that returns audio rather than an image, and the only one whose `save_to` writes a
    single file with no companion preview.

Long recordings are worked in windows: clip a few minutes, transcribe or label them, then move the
window on. Gemini bills audio at 32 tokens per second, so a 6-second clip is roughly 200 tokens —
cheap enough to re-listen to a segment during a correction round.

**Then**: [`clip_audio`](../mcp/tools.md#clip_audio) for the parameters and the error rules, and
[`clip_audio`](../api/audio.md#annotools.audio.clip_audio) plus
[`write_bytes`](../api/io.md#annotools.io.write_bytes) for the library contract. There is no
audio-specific skill yet; the store and pipeline conventions in
[`skills/sqlite-annotation-store`](https://github.com/hoshiori-dev/annotools/tree/main/skills/sqlite-annotation-store)
apply unchanged — keep the WAV on disk and store its path, never its bytes.
