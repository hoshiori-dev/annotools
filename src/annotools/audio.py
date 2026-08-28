"""Audio clipping and resampling via PyAV (``annotools[media]``)."""

import io
import wave
from contextlib import ExitStack
from typing import Any

import numpy as np

from annotools._media import open_container, require_av

__all__ = [
    "clip_audio",
]


def clip_audio(
    uri: str,
    *,
    start: float | None = None,
    end: float | None = None,
    sample_rate: int | None = None,
) -> tuple[bytes, dict[str, Any]]:
    """Cut ``[start, end)`` seconds from the first audio stream of ``uri`` and return 16-bit PCM WAV bytes.

    WAV keeps the clip self-describing and losslessly decodable by every audio model; resampling is
    optional so a caller can hit a model's expected rate (16 kHz for most speech models) in one step.

    Args:
        uri: Local path or fsspec URL of an audio or video file with an audio stream.
        start: Start time in seconds (>= 0); ``None`` = 0.
        end: End time in seconds (> ``start``); ``None`` = until the end.
        sample_rate: Output sample rate in Hz (>= 1); ``None`` keeps the source rate.

    Returns:
        ``(wav_bytes, metadata)`` with ``source_duration``, ``start``, ``end``, ``duration``,
        ``sample_rate``, and ``channels``.

    Raises:
        ValueError: For an invalid range or rate, a start beyond the source, a source without audio,
            or content that is not decodable; the message names the URI.
        FileNotFoundError: When the URI does not exist.
        OSError: For other read failures.
        ImportError: When PyAV is not installed (``annotools[media]``).

    Example:
        >>> from annotools import clip_audio
        >>> wav, meta = clip_audio(
        ...     "talk.wav", start=2, end=5, sample_rate=16000
        ... )  # doctest: +SKIP
        >>> meta["duration"], meta["sample_rate"]  # doctest: +SKIP
        (3.0, 16000)

    References:
        - Spec: ``.agents/knowledge/spec/clip-audio.md`` (annotools repository).
        - Gemini bills audio at 32 tokens per second: ``.agents/knowledge/references/mllm-models.md``
          (verified 2026-08-27).
    """
    if start is not None and start < 0:
        raise ValueError(f"start must be >= 0, got {start}")
    if end is not None and end <= (start or 0.0):
        raise ValueError(f"end ({end}) must be greater than start ({start or 0.0})")
    if sample_rate is not None and sample_rate < 1:
        raise ValueError(f"sample_rate must be >= 1, got {sample_rate}")
    av = require_av("audio")
    begin = start or 0.0
    with ExitStack() as stack:
        container = open_container(av, uri, stack)
        if not container.streams.audio:
            raise ValueError(f"{uri}: no audio stream")
        stream = container.streams.audio[0]
        source_duration = (
            float(stream.duration * stream.time_base)
            if stream.duration
            else (float(container.duration / av.time_base) if container.duration else 0.0)
        )
        if source_duration and begin >= source_duration:
            raise ValueError(f"start ({begin}) is beyond the source duration ({source_duration:.3f} s)")
        stop = min(end, source_duration) if end is not None and source_duration else end
        out_rate = sample_rate or stream.rate
        layout = stream.layout.name  # keep the source channel layout (mono, stereo, 5.1, ...)
        channels = stream.layout.nb_channels
        resampler = av.AudioResampler(format="s16", layout=layout, rate=out_rate)
        if begin > 0:
            container.seek(int(begin / stream.time_base), stream=stream, backward=True, any_frame=False)
        chunks: list[np.ndarray] = []
        for frame in container.decode(stream):
            t = float(frame.time) if frame.time is not None else 0.0
            frame_duration = frame.samples / frame.sample_rate
            if t + frame_duration <= begin:
                continue
            if stop is not None and t >= stop:
                break
            for out in resampler.resample(frame):
                pcm = out.to_ndarray()  # (channels, samples) for planar? s16 is packed: (1, samples*channels)
                pcm = pcm.reshape(-1, channels) if pcm.ndim == 2 and pcm.shape[0] == 1 else pcm.T
                out_t = float(out.time) if out.time is not None else t
                skip = round(max(0.0, begin - out_t) * out_rate)
                keep = pcm[skip:]
                if stop is not None:
                    limit = round(max(0.0, stop - max(out_t, begin)) * out_rate)
                    keep = keep[:limit]
                if len(keep):
                    chunks.append(keep.astype(np.int16))
        for out in resampler.resample(None):
            pcm = out.to_ndarray()
            pcm = pcm.reshape(-1, channels) if pcm.ndim == 2 and pcm.shape[0] == 1 else pcm.T
            chunks.append(pcm.astype(np.int16))
    samples = np.concatenate(chunks) if chunks else np.zeros((0, channels), dtype=np.int16)
    if stop is not None:
        samples = samples[: round((stop - begin) * out_rate)]
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(out_rate)
        wav.writeframes(samples.tobytes())
    duration = len(samples) / out_rate
    metadata = {
        "source_duration": round(source_duration, 3),
        "start": begin,
        "end": round(begin + duration, 3),
        "duration": round(duration, 3),
        "sample_rate": out_rate,
        "channels": channels,
    }
    return buffer.getvalue(), metadata
