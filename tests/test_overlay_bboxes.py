import json

import numpy as np
import pytest
from fastmcp import Client

from annotools.image.grid import GridOptions, draw_grid
from annotools.image.overlay import BBoxObject, draw_bboxes
from annotools.image.preview import preview
from tests.conftest import make_image

BLUE = (0, 0, 255)
WHITE = (255, 255, 255)


def pix(image, x: int, y: int) -> tuple[int, ...]:
    return tuple(int(v) for v in np.asarray(image.convert("RGB"))[y, x])


def render(width=768, height=768, crop=None, objects=(), **kwargs):
    result = preview(make_image(width, height), crop=crop)
    return draw_bboxes(result, list(objects), **kwargs)


def test_ac1_box_pixels():
    img = render(objects=[BBoxObject(bbox=(0.1, 0.1, 0.5, 0.5))]).image
    # edges at x=77..78 / y=77..78 and x=383..384 / y=383..384 (2 px band centred on 76.8 and 384)
    assert pix(img, 77, 200) == BLUE and pix(img, 383, 200) == BLUE
    assert pix(img, 200, 77) == BLUE and pix(img, 200, 383) == BLUE
    assert pix(img, 74, 200) == WHITE and pix(img, 81, 200) == WHITE
    assert pix(img, 200, 200) == WHITE


def test_ac2_label_rendered():
    plain = render(objects=[BBoxObject(bbox=(0.2, 0.2, 0.6, 0.6))]).image
    labeled = render(objects=[BBoxObject(bbox=(0.2, 0.2, 0.6, 0.6), label="cat")]).image
    above = np.asarray(labeled.convert("RGB"))[130:152, 154:220]
    assert (above != 255).any()
    assert (np.asarray(plain.convert("RGB"))[130:150, 154:220] == 255).all()


def test_ac3_crop_composition():
    img = render(800, 400, crop=(0.5, 0, 1, 1), objects=[BBoxObject(bbox=(0.5, 0, 1, 1))]).image
    assert img.size == (400, 400)
    assert pix(img, 0, 200) == BLUE and pix(img, 399, 200) == BLUE
    assert pix(img, 200, 0) == BLUE and pix(img, 200, 399) == BLUE
    assert pix(img, 200, 200) == WHITE


def test_ac4_colors():
    img = render(objects=[BBoxObject(bbox=(0.1, 0.1, 0.5, 0.5), color="red")]).image
    assert pix(img, 77, 200) == (255, 0, 0)
    img = render(objects=[BBoxObject(bbox=(0.1, 0.1, 0.5, 0.5), color="#00ff00")]).image
    assert pix(img, 77, 200) == (0, 255, 0)
    with pytest.raises(ValueError, match=r"objects\[0\]"):
        render(objects=[BBoxObject(bbox=(0.1, 0.1, 0.5, 0.5), color="not-a-color")])


def test_ac5_grid_plus_boxes():
    result = preview(make_image(768, 768))
    result.image = draw_grid(result.image, GridOptions(color="black")).image
    img = draw_bboxes(result, [BBoxObject(bbox=(0.1, 0.1, 0.5, 0.5))]).image
    assert pix(img, 77, 200) == BLUE


def test_ac6_empty_objects_raises():
    with pytest.raises(ValueError, match="objects"):
        render(objects=[])


async def test_ac7_tool(mcp_server, image_file):
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "preview_image_bboxes",
            {
                "source": str(image_file(400, 200)),
                "grid": {"columns": 4, "rows": 2},
                "objects": [{"bbox": [0, 0, 0.5, 0.5], "label": "a"}, {"bbox": [0.5, 0.5, 1, 1]}],
            },
        )
    meta = json.loads(result.content[1].text)
    assert meta["objects"] == 2 and meta["grid"]["columns"] == 4
