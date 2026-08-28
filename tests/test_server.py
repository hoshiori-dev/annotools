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
    assert {"preview_image", "preview_image_segmentation", "preview_video", "clip_audio", "color_from_text"} <= names
    assert len(names) == 13


def test_tool_modules_do_not_import_server():
    """Tool modules depend on ``annotools.app`` only, so there is no tools <-> server import cycle."""
    import subprocess
    import sys
    from pathlib import Path

    import annotools.tools

    for path in Path(annotools.tools.__file__).parent.glob("*.py"):
        assert "annotools.server" not in path.read_text(), path.name
    # A fresh interpreter importing a tool module before the server must not hit a partially initialised module.
    code = (
        "import asyncio, annotools.tools.image_tools; from annotools.server import mcp; "
        "print(len(asyncio.run(mcp.list_tools())))"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "13"
