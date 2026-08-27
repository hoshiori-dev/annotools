import json

import numpy as np
import pytest
from fastmcp import Client

from annotools.image.grid import GridOptions, draw_grid
from annotools.image.preview import encode, preview
from tests.conftest import make_image


def pix(image, x: int, y: int) -> tuple[int, ...]:
    return tuple(int(v) for v in np.asarray(image.convert("RGB"))[y, x])


def test_ac1_default_grid_line_positions():
    black = draw_grid(make_image(768, 768, "black"), GridOptions())
    img = black.image
    lines = [round(768 * i / 10) for i in range(1, 10)]
    for x in lines:
        assert pix(img, x, 300) in ((128, 128, 128), (127, 127, 127))
        assert pix(img, 300, x)[0] >= 127
    assert pix(img, 0, 300) == (0, 0, 0) and pix(img, 767, 300) == (0, 0, 0)
    assert pix(img, 40, 300) == (0, 0, 0)
    assert black.metadata["grid"] == {"columns": 10, "rows": 10, "step_x": 0.1, "step_y": 0.1}


@pytest.mark.parametrize("line_width", [1, 2, 3])
def test_line_width_is_exact(line_width):
    img = draw_grid(make_image(100, 100, "black"), GridOptions(columns=2, rows=1, line_width=line_width)).image
    row = np.asarray(img.convert("RGB"))[10, :, 0]
    assert int((row > 0).sum()) == line_width


def test_ac1_white_on_white_is_unchanged():
    img = draw_grid(make_image(100, 100, "white"), GridOptions()).image
    assert (np.asarray(img.convert("RGB")) == 255).all()


def test_ac2_fixed_mode():
    result = draw_grid(make_image(768, 512, "black"), GridOptions(mode="fixed", column_width=100, row_width=100))
    img = result.image
    assert pix(img, 100, 10)[0] >= 127 and pix(img, 700, 10)[0] >= 127 and pix(img, 50, 10) == (0, 0, 0)
    assert result.metadata["grid"]["columns"] == 8 and result.metadata["grid"]["rows"] == 6
    assert result.metadata["grid"]["step_x"] == pytest.approx(100 / 768)


def test_ac3_color_black_and_invert():
    img = draw_grid(make_image(100, 100, "white"), GridOptions(color="black")).image
    assert pix(img, 50, 25)[0] in (127, 128)
    img = draw_grid(make_image(100, 100, "red"), GridOptions(color="invert")).image
    r, g, b = pix(img, 50, 25)
    assert r in (127, 128) and g in (127, 128) and b in (127, 128)


def test_ac4_opacity_zero_is_noop():
    image = make_image(64, 48, "blue")
    plain = encode(preview(image).image, "png")
    gridded = encode(draw_grid(preview(image).image, GridOptions(opacity=0)).image, "png")
    assert plain == gridded


@pytest.mark.parametrize(
    "kwargs",
    [{"columns": 0}, {"opacity": 1.5}, {"mode": "fixed"}, {"mode": "fixed", "column_width": 0, "row_width": 10}],
    ids=["columns", "opacity", "fixed-no-widths", "fixed-zero-width"],
)
def test_ac5_invalid_options(kwargs):
    with pytest.raises(ValueError):
        draw_grid(make_image(10, 10), GridOptions(**kwargs))


async def test_ac6_tool_metadata(mcp_server, image_file):
    async with Client(mcp_server) as client:
        result = await client.call_tool("preview_image_grid", {"source": str(image_file(300, 150))})
    meta = json.loads(result.content[1].text)
    assert meta["grid"]["step_x"] == 0.1 and meta["grid"]["columns"] == 10
    assert meta["output_size"] == [300, 150]
