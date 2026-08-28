import base64
import io
import json
import sys
import wave

import numpy as np
import pytest
from fastmcp import Client
from mcp.types import AudioContent, TextContent

from annotools.audio import clip


@pytest.fixture(scope="module")
def audio_file(tmp_path_factory):
    """10-second 440 Hz mono tone at 44.1 kHz as a WAV file."""
    path = tmp_path_factory.mktemp("audio") / "tone.wav"
    rate = 44100
    t = np.arange(rate * 10) / rate
    samples = (np.sin(2 * np.pi * 440 * t) * 12000).astype(np.int16)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(samples.tobytes())
    return path


def wav_info(data: bytes) -> tuple[float, int, int]:
    with wave.open(io.BytesIO(data)) as wav:
        return wav.getnframes() / wav.getframerate(), wav.getframerate(), wav.getnchannels()


def test_ac1_clip_bounds(audio_file):
    data, meta = clip(str(audio_file), start=2, end=5)
    duration, rate, channels = wav_info(data)
    assert duration == pytest.approx(3.0, abs=0.05)
    assert meta["duration"] == pytest.approx(duration, abs=0.01)
    assert meta["source_duration"] == pytest.approx(10.0, abs=0.05)
    assert (rate, channels) == (44100, 1)


def test_ac2_resample(audio_file):
    data, meta = clip(str(audio_file), start=0, end=1, sample_rate=8000)
    duration, rate, _ = wav_info(data)
    assert rate == 8000 and meta["sample_rate"] == 8000
    assert duration == pytest.approx(1.0, abs=0.05)
    assert wav_info(clip(str(audio_file), end=1)[0])[1] == 44100


def test_ac6_multichannel_kept(tmp_path):
    path = tmp_path / "six.wav"
    rate = 16000
    frames = np.tile(np.arange(6, dtype=np.int16) * 1000, (rate * 2, 1))  # 2 s, channel i holds value i*1000
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(6)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(frames.tobytes())
    data, meta = clip(str(path), start=0.5, end=1.5)
    duration, out_rate, channels = wav_info(data)
    assert (channels, out_rate, meta["channels"]) == (6, rate, 6)
    assert duration == pytest.approx(1.0, abs=0.01)
    with wave.open(io.BytesIO(data)) as wav:
        first = np.frombuffer(wav.readframes(1), dtype=np.int16)
    assert first.tolist() == [0, 1000, 2000, 3000, 4000, 5000]


def test_ac7_errors_name_source(tmp_path, audio_file):
    junk = tmp_path / "junk.bin"
    junk.write_bytes(bytes(range(256)) * 64)  # random-looking bytes: no demuxer accepts them
    with pytest.raises(ValueError, match=r"junk\.bin"):
        clip(str(junk))
    with pytest.raises(ValueError, match=r"end \(0\)"):
        clip(str(audio_file), end=0)
    with pytest.raises(FileNotFoundError, match=r"missing\.wav"):
        clip(str(tmp_path / "missing.wav"))


def test_sample_exact_length(audio_file):
    data, _ = clip(str(audio_file), end=3)
    with wave.open(io.BytesIO(data)) as wav:
        assert wav.getnframes() == 3 * 44100


@pytest.mark.parametrize("kwargs", [{"start": 5, "end": 5}, {"start": -1}, {"start": 20}, {"sample_rate": 0}])
def test_ac3_invalid_range(audio_file, kwargs):
    with pytest.raises(ValueError):
        clip(str(audio_file), **kwargs)


async def test_ac4_and_ac5_tool(mcp_server, audio_file, tmp_path):
    out = tmp_path / "clip.wav"
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "clip_audio", {"source": str(audio_file), "start": 2, "end": 5, "save_to": str(out)}
        )
    audio, text = result.content
    assert isinstance(audio, AudioContent) and audio.mimeType == "audio/wav"
    assert isinstance(text, TextContent)
    assert out.read_bytes() == base64.b64decode(audio.data)
    meta = json.loads(text.text)
    assert meta["duration"] == pytest.approx(3.0, abs=0.05) and meta["saved_to"] == str(out)


def test_missing_media_extra_names_it(monkeypatch, audio_file):
    monkeypatch.setitem(sys.modules, "av", None)
    with pytest.raises(ImportError, match=r"annotools\[media\]"):
        clip(str(audio_file))


def test_unknown_protocol_raises_oserror_naming_the_uri():
    with pytest.raises(OSError, match=r"nope://clip\.wav"):
        clip("nope://clip.wav")


def test_video_without_audio_stream_is_rejected(tmp_path):
    import av

    path = tmp_path / "silent.mp4"
    with av.open(str(path), "w") as container:
        stream = container.add_stream("mpeg4", rate=10)
        stream.width, stream.height = 64, 48
        stream.pix_fmt = "yuv420p"
        for _ in range(5):
            frame = np.zeros((48, 64, 3), dtype=np.uint8)
            for packet in stream.encode(av.VideoFrame.from_ndarray(frame, format="rgb24")):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    with pytest.raises(ValueError, match="no audio stream"):
        clip(str(path))


def test_start_beyond_duration_is_rejected(audio_file):
    with pytest.raises(ValueError, match="beyond the source duration"):
        clip(str(audio_file), start=20)


def test_late_window_skips_frames_before_start(audio_file):
    data, meta = clip(str(audio_file), start=5.0, end=5.5)
    duration, _rate, _channels = wav_info(data)
    assert abs(duration - 0.5) < 0.01 and meta["start"] == 5.0
