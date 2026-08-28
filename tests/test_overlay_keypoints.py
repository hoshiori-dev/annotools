import json

import numpy as np
import pytest
from fastmcp import Client

from annotools.image.overlay import KeypointObject, draw_keypoints
from annotools.image.preview import preview
from tests.conftest import make_image

BLUE = (0, 0, 255)
WHITE = (255, 255, 255)


def pix(image, x: int, y: int) -> tuple[int, ...]:
    return tuple(int(v) for v in np.asarray(image.convert("RGB"))[y, x])


def render(width=768, height=768, crop=None, objects=(), **kwargs):
    return draw_keypoints(
        preview(make_image(width, height), crop=crop, max_width=768, max_height=768), list(objects), **kwargs
    )


def test_ac1_dot_pixels():
    img = render(objects=[KeypointObject(point=(0.5, 0.5))]).image
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        assert pix(img, 384 + dx, 384 + dy) == BLUE
    assert pix(img, 388, 384) == WHITE and pix(img, 384, 380) == WHITE


def test_ac2_label_offset():
    img = render(objects=[KeypointObject(point=(0.5, 0.5), label="nose")]).image
    assert pix(img, 384, 384) == BLUE
    right = np.asarray(img.convert("RGB"))[370:400, 388:440]
    assert (right != 255).any()


def test_point_on_source_edge_is_drawn():
    img = render(objects=[KeypointObject(point=(1.0, 0.5))]).image
    assert pix(img, 767, 384) == BLUE


def test_ac3_out_of_range_raises():
    with pytest.raises(ValueError, match=r"objects\[0\]\.point"):
        render(objects=[KeypointObject(point=(1.2, 0.5))])


def test_ac4_crop_composition():
    img = render(800, 400, crop=(0.5, 0, 1, 1), objects=[KeypointObject(point=(0.25, 0.5))]).image
    assert (np.asarray(img.convert("RGB")) == 255).all()
    img = render(800, 400, crop=(0.5, 0, 1, 1), objects=[KeypointObject(point=(0.75, 0.5))]).image
    assert pix(img, 200, 200) == BLUE


async def test_ac5_tool(mcp_server, image_file):
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "preview_image_keypoints",
            {
                "source": str(image_file(400, 200)),
                "objects": [{"point": [0.1, 0.1]}, {"point": [0.9, 0.9], "label": "b"}],
            },
        )
    assert json.loads(result.content[1].text)["objects"] == 2


def test_empty_objects_and_small_diameter_raise():
    with pytest.raises(ValueError, match="at least one keypoint"):
        render(objects=[])
    with pytest.raises(ValueError, match="point_diameter"):
        render(objects=[KeypointObject(point=[0.5, 0.5])], point_diameter=0)
