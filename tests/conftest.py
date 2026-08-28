import pytest
from PIL import Image


@pytest.fixture
def mcp_server():
    from annotools.mcp.server import mcp

    return mcp


def make_image(width: int, height: int, color: str | int | tuple[int, ...] = "white", mode: str = "RGB") -> Image.Image:
    return Image.new(mode, (width, height), color)


@pytest.fixture
def image_file(tmp_path):
    """Factory writing a generated image to disk and returning its path."""

    def _make(width: int, height: int, name: str = "img.png", color: str = "white"):
        path = tmp_path / name
        make_image(width, height, color).save(path)
        return path

    return _make
