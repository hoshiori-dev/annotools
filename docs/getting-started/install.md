---
icon: lucide/download
---

# Install

annotools needs Python 3.12 or newer. Install from git: the first full release publishes to PyPI, and
until then only pre-releases exist. Every release is also uploaded to TestPyPI, which rehearses the
publishing path rather than serving installs — its dependency resolution is incomplete, so install from
git instead, including pre-releases.

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

Or run the published container, which carries the `media` extra (but not `remote`, so `s3://` and
`gs://` sources are not available inside it):

```bash
docker run --rm -i -v "$PWD:/data" ghcr.io/hoshiori-dev/annotools:0.1.0-rc1
```

Only the `0.1.0-rc1` pre-release image exists so far; `latest` and the `<major>.<minor>` tags are
published by the first full release. A `nightly` tag tracks `main` — built, smoke-tested and scanned
every night, but unreleased, so treat it as a preview. The image is not yet anonymously pullable — see
[#93](https://github.com/hoshiori-dev/annotools/issues/93).

The container's working directory is `/data`, so a source path an agent passes is resolved relative to
the directory you mounted there — an absolute host path will not resolve inside the container.

Next: [register the server](register.md) with your coding agent.
