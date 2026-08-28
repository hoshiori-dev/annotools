---
icon: lucide/download
---

# Install

annotools needs Python 3.12 or newer. PyPI publishing is not enabled yet, so install from git.

## As a library

```bash
uv add "annotools @ git+https://github.com/hoshiori-dev/annotools"
```

```bash
pip install "annotools @ git+https://github.com/hoshiori-dev/annotools"
```

Two extras are available, neither installed by default:

| Extra | Adds | Needed for |
|---|---|---|
| `media` | PyAV | [`sample_frames`](../api/video.md), [`clip_audio`](../api/audio.md), and the `preview_video*` / `clip_audio` MCP tools |
| `remote` | s3fs, gcsfs, aiohttp, requests | reading sources from `s3://`, `gs://` and `https://` URLs |

```bash
uv add "annotools[media,remote] @ git+https://github.com/hoshiori-dev/annotools"
```

Importing `annotools` works without either extra: PyAV is imported lazily, so only the video and audio
functions raise `ImportError` (naming `annotools[media]`) when it is missing.

## As an MCP server

The same package ships the `annotools` command, which is the MCP server:

```bash
uv run annotools --help
```

Or run the published container, which already has the `media` extra:

```bash
docker run --rm -i -v "$PWD:/data" ghcr.io/hoshiori-dev/annotools
```

The container's working directory is `/data`, so a source path an agent passes is resolved relative to
the directory you mounted there.

Next: [register the server](register.md) with your coding agent.
