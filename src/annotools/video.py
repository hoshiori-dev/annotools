"""Frame sampling from video files via PyAV (``annotools[media]``)."""

from contextlib import ExitStack
from typing import Any

from PIL import Image

from annotools._media import open_container, require_av

__all__ = [
    "sample_frames",
]


def sample_frames(
    uri: str,
    *,
    fps: float = 1.0,
    start: float | None = None,
    end: float | None = None,
    max_frames: int = 32,
) -> tuple[list[tuple[float, Image.Image]], dict[str, Any]]:
    """Decode ``uri`` and return frames sampled at ``fps`` between ``start`` and ``end``.

    Frames are picked at the first decoded timestamp at or after each target time, then thinned
    evenly to ``max_frames`` (first and last kept when ``max_frames > 1``) so a long clip cannot blow the
    token budget; feed the result through
    :func:`preview` (and a grid) before sending it to a model that has no native video input.

    Args:
        uri: Local path or fsspec URL of a video PyAV can decode.
        fps: Target sampling rate in frames per second (> 0).
        start: Start time in seconds (>= 0); ``None`` = 0.
        end: End time in seconds (> ``start``); ``None`` = until the end.
        max_frames: Upper bound on returned frames (>= 1).

    Returns:
        ``(frames, metadata)`` where ``frames`` is a list of ``(timestamp_seconds, PIL image)`` and
        ``metadata`` has ``duration``, ``requested_fps``, and ``thinned``.

    Raises:
        ValueError: For an invalid range, rate, or ``max_frames``, a source without a video stream, or a
            window with no frames; the message names the URI.
        FileNotFoundError: When the URI does not exist.
        OSError: For other read failures.
        ImportError: When PyAV is not installed (``annotools[media]``).

    Example:
        >>> from annotools import sample_frames
        >>> frames, meta = sample_frames("clip.mp4", fps=1, end=5)  # doctest: +SKIP
        >>> [round(t) for t, _ in frames]  # doctest: +SKIP
        [0, 1, 2, 3, 4]

    References:
        - Spec: ``.agents/knowledge/spec/preview-video.md`` (annotools repository).
        - Claude and GPT accept no native video in the vision path (send frames); Gemini samples video
          at 1 fps, 258 tokens per frame: ``.agents/knowledge/references/mllm-models.md`` (verified
          2026-08-27).
    """
    if fps <= 0:
        raise ValueError(f"fps must be > 0, got {fps}")
    if start is not None and start < 0:
        raise ValueError(f"start must be >= 0, got {start}")
    if end is not None and end <= (start or 0.0):
        raise ValueError(f"end ({end}) must be greater than start ({start or 0.0})")
    if max_frames < 1:
        raise ValueError(f"max_frames must be >= 1, got {max_frames}")
    av = require_av("video")
    begin = start or 0.0
    with ExitStack() as stack:
        container = open_container(av, uri, stack)
        if not container.streams.video:
            raise ValueError(f"{uri}: no video stream")
        stream = container.streams.video[0]
        stream.thread_type = "AUTO"
        duration = (
            float(stream.duration * stream.time_base)
            if stream.duration
            else (float(container.duration / av.time_base) if container.duration else 0.0)
        )
        stop = end if end is not None else float("inf")
        if begin > 0:
            container.seek(int(begin / stream.time_base), stream=stream, backward=True, any_frame=False)
        selected: list[tuple[float, Image.Image]] = []
        next_target = begin
        for frame in container.decode(stream):
            t = float(frame.time) if frame.time is not None else 0.0
            if t >= stop:
                break
            if t + 1e-6 >= next_target:
                selected.append((t, frame.to_image()))
                next_target += 1 / fps
                while next_target <= t:
                    next_target += 1 / fps
    if not selected:
        until = end if end is not None else "the end"
        raise ValueError(f"{uri}: no frames between {begin} s and {until} (duration {duration:.3f} s)")
    thinned = len(selected) > max_frames
    if thinned:
        step = (len(selected) - 1) / (max_frames - 1) if max_frames > 1 else 0
        selected = [selected[round(i * step)] for i in range(max_frames)]
    return selected, {"duration": duration, "requested_fps": fps, "thinned": thinned}
