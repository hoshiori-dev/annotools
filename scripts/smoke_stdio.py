"""Smoke test an installed ``annotools`` executable over stdio.

Usage: smoke_stdio.py /path/to/annotools
Exits non-zero unless the server answers ping and lists its tools.
"""

import asyncio
import sys

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


async def main(executable: str) -> None:
    """Connect over stdio, ping, and list tools."""
    async with Client(StdioTransport(command=executable, args=[])) as client:
        await client.ping()
        tools = await client.list_tools()
    print(f"ok: {len(tools)} tools")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
