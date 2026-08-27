import pytest
from fastmcp import Client


@pytest.mark.asyncio
async def test_server_starts_and_lists_tools(mcp_server):
    async with Client(mcp_server) as client:
        await client.ping()
        tools = await client.list_tools()
    assert isinstance(tools, list)
