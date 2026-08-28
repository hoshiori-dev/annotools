import pytest
from fastmcp import Client


@pytest.mark.asyncio
async def test_server_starts_and_lists_tools(mcp_server):
    async with Client(mcp_server) as client:
        await client.ping()
        tools = await client.list_tools()
    assert isinstance(tools, list)


@pytest.mark.asyncio
async def test_server_registers_all_tool_modules(mcp_server):
    async with Client(mcp_server) as client:
        names = {t.name for t in await client.list_tools()}
    # One tool per module under annotools.tools, so every module's registration is observed.
    assert {"preview_image", "preview_video", "clip_audio", "color_from_text", "normalize_coordinates"} <= names


def test_tool_modules_do_not_import_server():
    """Tool modules depend on ``annotools.app`` only, so there is no tools <-> server import cycle."""
    import re
    import subprocess
    import sys
    from pathlib import Path

    import annotools.tools

    for path in Path(annotools.tools.__file__).parent.glob("*.py"):
        assert not re.search(r"^(from|import) annotools\.server\b", path.read_text(), re.MULTILINE), path.name
    # A fresh interpreter importing a tool module before the server must not hit a partially initialised module.
    code = (
        "import asyncio, annotools.tools.image_tools; from annotools.server import mcp; "
        "print(len(asyncio.run(mcp.list_tools())))"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert int(result.stdout) > 0
