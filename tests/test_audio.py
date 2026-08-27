import base64
import io
import json
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
