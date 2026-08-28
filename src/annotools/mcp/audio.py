"""Audio tools."""

import json
from typing import Annotated

from fastmcp.utilities.types import Audio as McpAudio
from pydantic import Field

from annotools.audio import clip_audio as _clip_audio
from annotools.io import write_bytes
from annotools.mcp.app import mcp
from annotools.mcp.common import SourceParam

SaveWavParam = Annotated[str | None, Field(description="Also write the WAV file to this path or fsspec URL")]


@mcp.tool(output_schema=None)
def clip_audio(
    source: SourceParam,
    start: Annotated[float | None, Field(ge=0, description="Start time in seconds")] = None,
    end: Annotated[float | None, Field(gt=0, description="End time in seconds (exclusive)")] = None,
    sample_rate: Annotated[
        int | None, Field(ge=1, description="Resample to this rate; omit to keep the source rate")
    ] = None,
    save_to: SaveWavParam = None,
) -> list[McpAudio | str]:
    """Cut a segment from an audio (or video) file, optionally resampled, and return it as 16-bit WAV.

    Returns the audio followed by one JSON metadata object (source_duration, start, end, duration,
    sample_rate, channels).
    """
    data, metadata = _clip_audio(source, start=start, end=end, sample_rate=sample_rate)
    metadata["format"] = "wav"
    if save_to:
        write_bytes(save_to, data)
        metadata["saved_to"] = save_to
    return [McpAudio(data=data, format="wav"), json.dumps(metadata)]
