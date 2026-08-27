import pytest


@pytest.fixture
def mcp_server():
    from annotools.server import mcp

    return mcp
