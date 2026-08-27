import colorsys
import re

from fastmcp import Client

from annotools.color import color_from_text


def test_ac1_deterministic():
    assert color_from_text("cat") == color_from_text("cat")


def test_ac2_small_change_differs():
    assert color_from_text("cat") != color_from_text("cat ")
    assert color_from_text("") != color_from_text("a")


def test_ac3_saturation_and_lightness():
    for i in range(100):
        r, g, b = color_from_text(f"label-{i}-{i * i}")
        _h, lightness, saturation = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        assert saturation >= 0.7
        assert 0.45 <= lightness <= 0.55


async def test_ac4_tool(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool("color_from_text", {"text": "cat"})
    data = result.structured_content
    assert re.fullmatch(r"#[0-9a-f]{6}", data["hex"])
    assert len(data["rgb"]) == 3 and all(0 <= v <= 255 for v in data["rgb"])
    assert data["hex"] == "#{:02x}{:02x}{:02x}".format(*data["rgb"])
