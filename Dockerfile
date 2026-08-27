# syntax=docker/dockerfile:1
# Builds the annotools MCP server image. Default entrypoint speaks stdio; pass `--http` to serve HTTP on 8000.

FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.6 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project --extra media
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --extra media

FROM python:3.12-slim
RUN useradd --create-home --uid 1000 annotools
COPY --from=builder --chown=annotools:annotools /app /app
ENV PATH="/app/.venv/bin:$PATH"
USER annotools
WORKDIR /data
EXPOSE 8000
ENTRYPOINT ["annotools"]
