"""Frame sampling from video files via PyAV (``annotools[media]``)."""

from contextlib import ExitStack
from typing import Any

import fsspec
from PIL import Image


def _av():
    try:
        import av
    except ImportError as exc:
        raise ImportError("video support requires PyAV: install annotools[media]") from exc
    return av


def _open_container(av, uri: str, stack: ExitStack):
    """Open ``uri`` with PyAV through an fsspec file handle (streamed, not buffered in memory).

    Raises:
        FileNotFoundError / OSError: as ``annotools.io.open_bytes`` for unreadable sources.
        ValueError: naming the URI when the content is not a decodable media file.
    """
    try:
        handle = stack.enter_context(fsspec.open(uri, "rb"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"cannot read {uri}: not found") from exc
    except Exception as exc:  # backend-specific errors share no base class
        raise OSError(f"cannot read {uri}: {exc}") from exc
    try:
        return stack.enter_context(av.open(handle))
    except Exception as exc:
        raise ValueError(f"{uri}: not a decodable media file ({exc})") from exc


def sample_frames(
    uri: str,
    *,
    fps: float = 1.0,
    start: float | None = None,
    end: float | None = None,
    max_frames: int = 32,
) -> tuple[list[tuple[float, Image.Image]], dict[str, Any]]:
    """Sample frames at ``fps`` between ``start`` and ``end`` seconds, capped at ``max_frames``.

    Returns ``(frames, info)`` where ``frames`` is a list of ``(timestamp_seconds, PIL image)`` in time
    order and ``info`` has ``duration``, ``requested_fps``, and ``thinned``.

    Raises:
        ValueError: for invalid parameters or a source without a video stream.
        ImportError: when PyAV is not installed.
    """
    if fps <= 0:
        raise ValueError(f"fps must be > 0, got {fps}")
    if start is not None and start < 0:
        raise ValueError(f"start must be >= 0, got {start}")
    if end is not None and end <= (start or 0.0):
        raise ValueError(f"end ({end}) must be greater than start ({start or 0.0})")
    if max_frames < 1:
        raise ValueError(f"max_frames must be >= 1, got {max_frames}")
    av = _av()
    begin = start or 0.0
    with ExitStack() as stack:
        container = _open_container(av, uri, stack)
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
