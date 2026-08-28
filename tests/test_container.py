"""Container smoke tests: require a docker daemon and an image built with `just docker-build`."""

import asyncio
import os
import shutil
import subprocess
import uuid

import pytest
from fastmcp import Client

pytestmark = [pytest.mark.container, pytest.mark.skipif(shutil.which("docker") is None, reason="docker not available")]
IMAGE = os.environ.get("ANNOTOOLS_IMAGE", "annotools:dev")
PORT = 18765


def test_image_prints_help():
    result = subprocess.run(["docker", "run", "--rm", IMAGE, "--help"], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert "--http" in result.stdout


async def test_http_server_answers_ping():
    name = f"annotools-smoke-{uuid.uuid4().hex[:8]}"
    subprocess.run(  # noqa: ASYNC221 - the container is started once, before the async client connects
        ["docker", "run", "-d", "--rm", "--name", name, "-p", f"{PORT}:8000", IMAGE, "--http", "--host", "0.0.0.0"],
        check=True,
        capture_output=True,
    )
    try:
        last_error: Exception | None = None
        for _ in range(30):
            try:
                async with Client(f"http://127.0.0.1:{PORT}/mcp") as client:
                    await client.ping()
                    tools = await client.list_tools()
                assert isinstance(tools, list)
                return
            except Exception as exc:  # noqa: BLE001 - any failure means the server is not ready yet
                last_error = exc
                await asyncio.sleep(1)
        raise AssertionError(f"server never became ready: {last_error}")
    finally:
        subprocess.run(  # noqa: ASYNC221 - teardown, after the async client has already been closed
            ["docker", "rm", "-f", name], check=False, capture_output=True
        )
