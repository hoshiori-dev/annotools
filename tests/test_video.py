import json
import sys

import numpy as np
import pytest
from fastmcp import Client
from mcp.types import ImageContent, TextContent

from annotools.video import sample_frames


@pytest.fixture(scope="module")
def video_file(tmp_path_factory):
    """5-second 10 fps synthetic mp4 whose frame brightness encodes time."""
    import av

    path = tmp_path_factory.mktemp("video") / "clip.mp4"
    with av.open(str(path), "w") as container:
        stream = container.add_stream("mpeg4", rate=10)
        stream.width, stream.height = 320, 240
        stream.pix_fmt = "yuv420p"
        for i in range(50):
            frame = np.full((240, 320, 3), min(255, i * 5), dtype=np.uint8)
            for packet in stream.encode(av.VideoFrame.from_ndarray(frame, format="rgb24")):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    return path


@pytest.fixture(scope="module")
def hd_video_file(tmp_path_factory):
    import av

    path = tmp_path_factory.mktemp("video") / "hd.mp4"
    with av.open(str(path), "w") as container:
        stream = container.add_stream("mpeg4", rate=2)
        stream.width, stream.height = 1920, 1080
        stream.pix_fmt = "yuv420p"
        for _ in range(4):
            frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
            for packet in stream.encode(av.VideoFrame.from_ndarray(frame, format="rgb24")):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    return path


def test_ac1_default_fps(video_file):
    frames, info = sample_frames(str(video_file))
    assert [round(t) for t, _ in frames] == [0, 1, 2, 3, 4]
    assert all(abs(t - round(t)) <= 0.1 for t, _ in frames)
    assert info["thinned"] is False and abs(info["duration"] - 5.0) < 0.2


def test_ac2_start_end(video_file):
    frames, _ = sample_frames(str(video_file), start=1, end=3)
    assert [round(t) for t, _ in frames] == [1, 2]


def test_ac3_max_frames_thinning(video_file):
    frames, info = sample_frames(str(video_file), fps=10, max_frames=8)
    assert len(frames) == 8 and info["thinned"] is True
    times = [t for t, _ in frames]
    assert times[0] == pytest.approx(0, abs=0.05)
    gaps = np.diff(times)
    assert gaps.max() - gaps.min() <= 0.15


@pytest.mark.parametrize("kwargs", [{"fps": 0}, {"start": -1}, {"start": 2, "end": 1}, {"max_frames": 0}])
def test_invalid_params(video_file, kwargs):
    with pytest.raises(ValueError):
        sample_frames(str(video_file), **kwargs)


def test_ac5_missing_extra(monkeypatch, video_file):
    monkeypatch.setitem(sys.modules, "av", None)
    with pytest.raises(ImportError, match=r"annotools\[media\]"):
        sample_frames(str(video_file))


async def test_ac4_and_ac6_tool(mcp_server, hd_video_file):
    async with Client(mcp_server) as client:
        result = await client.call_tool("preview_video_grid", {"source": str(hd_video_file), "fps": 1})
    *images, text = result.content
    assert all(isinstance(i, ImageContent) for i in images) and isinstance(text, TextContent)
    meta = json.loads(text.text)
    assert meta["frames"] == len(images) == 2
    assert meta["output_size"] == [384, 216] and meta["grid"]["columns"] == 10
    assert (meta["output_width"], meta["output_height"], meta["original_width"]) == (384, 216, 1920)
    assert meta["grid"]["cell_width"] == pytest.approx(38.4) and meta["grid"]["cell_height"] == pytest.approx(21.6)
    assert meta["timestamps"][0] == pytest.approx(0, abs=0.05)


async def test_ac6_plain_tool_and_ac7_save_to_directory(mcp_server, video_file, tmp_path):
    out = tmp_path / "frames"
    async with Client(mcp_server) as client:
        result = await client.call_tool("preview_video", {"source": str(video_file), "fps": 1, "save_to": str(out)})
    *images, text = result.content
    meta = json.loads(text.text)
    assert meta["frames"] == len(images) == 5 and "grid" not in meta
    assert meta["saved_to"] == str(out)
    assert min(p.name for p in out.iterdir()) == "frame_0000_0.000.jpeg"
    assert meta["output_size"] == [320, 240]


def test_ac8_errors_name_source(tmp_path, video_file):
    text = tmp_path / "notes.txt"
    text.write_text("not a video")
    with pytest.raises(ValueError, match=r"notes\.txt"):
        sample_frames(str(text))
    with pytest.raises(ValueError, match=r"clip\.mp4.*no frames"):
        sample_frames(str(video_file), start=4.99, end=4.995)
    with pytest.raises(ValueError, match=r"end \(0\)"):
        sample_frames(str(video_file), end=0)
    with pytest.raises(FileNotFoundError, match=r"missing\.mp4"):
        sample_frames(str(tmp_path / "missing.mp4"))


def test_audio_only_source_raises(tmp_path):
    import wave

    path = tmp_path / "tone.wav"
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(bytes(16000))
    with pytest.raises(ValueError, match=r"tone\.wav: no video stream"):
        sample_frames(str(path))
