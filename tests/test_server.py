import re
import subprocess
import sys
from pathlib import Path

import pytest
from fastmcp import Client

import annotools.mcp

MCP_DIR = Path(annotools.mcp.__file__).parent
TOOL_MODULES = ("audio", "color", "geometry", "image", "video")
INFRASTRUCTURE = ("__init__", "app", "cli", "common", "server")


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
    # One tool per module under annotools.mcp, so every module's registration is observed.
    assert {"preview_image", "preview_video", "clip_audio", "color_from_text", "normalize_coordinates"} <= names


def test_every_mcp_module_is_a_known_tool_module_or_infrastructure():
    """A new tool module must be added to TOOL_MODULES (and to the server's import line)."""
    on_disk = {path.stem for path in MCP_DIR.glob("*.py")}
    assert on_disk == set(TOOL_MODULES) | set(INFRASTRUCTURE)


def test_tool_modules_do_not_import_server_and_app_imports_no_tool_module():
    """Tool modules depend on ``annotools.mcp.app`` only; ``app``/``common`` never import a tool module."""
    for stem in (*TOOL_MODULES, "app", "common"):
        text = (MCP_DIR / f"{stem}.py").read_text()
        assert not re.search(r"^(from|import) annotools\.mcp\.server\b", text, re.MULTILINE), stem
    for stem in ("app", "common"):
        text = (MCP_DIR / f"{stem}.py").read_text()
        for tool in TOOL_MODULES:
            assert not re.search(rf"^(from|import) annotools\.mcp\.{tool}\b", text, re.MULTILINE), (stem, tool)
            assert not re.search(rf"^from annotools\.mcp import .*\b{tool}\b", text, re.MULTILINE), (stem, tool)
    # A fresh interpreter importing a tool module before the server must not hit a partially initialised module.
    code = (
        "import asyncio, annotools.mcp.image; from annotools.mcp.server import mcp; "
        "print(len(asyncio.run(mcp.list_tools())))"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert int(result.stdout) == 13


def test_library_import_does_not_load_fastmcp():
    """The library layer stays usable without the MCP stack (ARCHITECTURE.md decision)."""
    code = (
        "import sys, annotools, annotools.image.preview, annotools.geometry; "
        "print('fastmcp' in sys.modules, 'annotools.mcp' in sys.modules)"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["False", "False"]
