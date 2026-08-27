import json

from fastmcp import Client
from mcp.types import ImageContent, TextContent


async def test_ac7_tool_returns_image_and_metadata(mcp_server, image_file):
    path = image_file(1600, 1200)
    async with Client(mcp_server) as client:
        result = await client.call_tool("preview_image", {"source": str(path)})
    image, text = result.content
    assert isinstance(image, ImageContent) and image.mimeType == "image/jpeg"
    assert isinstance(text, TextContent)
    meta = json.loads(text.text)
    assert meta["original_size"] == [1600, 1200]
    assert meta["output_size"] == [768, 576]
    assert meta["crop"] == [0, 0, 1, 1]
    assert meta["format"] == "jpeg"


async def test_ac8_save_to_writes_file(mcp_server, image_file, tmp_path):
    path = image_file(100, 50)
    out = tmp_path / "preview.png"
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "preview_image", {"source": str(path), "output_format": "png", "save_to": str(out)}
        )
    import base64

    assert out.read_bytes() == base64.b64decode(result.content[0].data)
    assert json.loads(result.content[1].text)["saved_to"] == str(out)


async def test_invalid_crop_is_tool_error(mcp_server, image_file):
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "preview_image", {"source": str(image_file(10, 10)), "crop": [0.5, 0, 0.5, 1]}, raise_on_error=False
        )
    assert result.is_error
    assert "crop" in result.content[0].text
