import json

import numpy as np
import pytest
from fastmcp import Client

from annotools.image.overlay import PolygonObject, draw_polygons
from annotools.image.preview import preview
from tests.conftest import make_image

BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
TRIANGLE = [0.1, 0.1, 0.5, 0.1, 0.1, 0.5]


def pix(image, x: int, y: int) -> tuple[int, ...]:
    return tuple(int(v) for v in np.asarray(image.convert("RGB"))[y, x])


def near(image, x: int, y: int, color, radius: int = 2) -> bool:
    """Whether ``color`` appears within ``radius`` px of (x, y) — line rasterization may shift by a pixel."""
    window = np.asarray(image.convert("RGB"))[y - radius : y + radius + 1, x - radius : x + radius + 1]
    return bool((window == np.array(color)).all(axis=-1).any())


def render(objects, **kwargs):
    return draw_polygons(preview(make_image(768, 768), max_width=768, max_height=768), objects, **kwargs).image


def test_ac1_outline_and_vertices():
    img = render([PolygonObject(points=TRIANGLE)])
    assert near(img, 230, 77, BLUE)  # midpoint of the top edge (y = 76.8)
    assert near(img, 77, 230, BLUE)  # midpoint of the left edge
    assert near(img, 230, 230, BLUE)  # midpoint of the hypotenuse
    for vx, vy in ((77, 77), (384, 77), (77, 384)):
        assert near(img, vx, vy, BLUE)
    assert pix(img, 180, 180) == WHITE


def test_ac2_point_indices():
    with_idx = np.asarray(render([PolygonObject(points=TRIANGLE)]).convert("RGB"))
    without = np.asarray(render([PolygonObject(points=TRIANGLE)], show_point_index=False).convert("RGB"))
    # a 40x40 window around the first vertex minus the dot/edges shows index text only with indices on
    assert (with_idx[40:74, 40:74] != 255).any()
    assert (without[40:74, 40:74] == 255).all()


@pytest.mark.parametrize("points", [[0.1, 0.1, 0.5, 0.1, 0.1], [0.1, 0.1, 0.5, 0.5]], ids=["odd", "two-points"])
def test_ac3_odd_count_raises(points):
    with pytest.raises(ValueError, match=r"objects\[0\]\.points"):
        render([PolygonObject(points=points)])


def test_ac4_rotated_box_roundtrip():
    img = render([PolygonObject(points=[0.2, 0.2, 0.6, 0.2, 0.6, 0.4, 0.2, 0.4])], show_point_index=False)
    assert near(img, 307, 154, BLUE) and near(img, 307, 307, BLUE)
    assert near(img, 154, 230, BLUE) and near(img, 461, 230, BLUE)
    assert pix(img, 307, 230) == WHITE


async def test_ac5_tool(mcp_server, image_file):
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "preview_image_polygons",
            {"source": str(image_file(400, 200)), "grid": {}, "objects": [{"points": TRIANGLE, "label": "roof"}]},
        )
    meta = json.loads(result.content[1].text)
    assert meta["objects"] == 1 and meta["grid"]["columns"] == 10


def test_label_at_top_edge_stays_inside():
    pts = [0, 0, 0.5, 0, 0.25, 0.4]
    plain = np.asarray(render([PolygonObject(points=pts)], show_point_index=False).convert("RGB"))
    labeled = np.asarray(render([PolygonObject(points=pts, label="roof")], show_point_index=False).convert("RGB"))
    assert (plain != labeled).any()
