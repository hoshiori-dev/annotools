import math

import pytest
from fastmcp import Client

from annotools.geometry import RotatedBox, is_rectangle, rotated_box_to_corners


def approx_list(values, expected):
    assert len(values) == len(expected)
    for v, e in zip(values, expected, strict=True):
        assert v == pytest.approx(e, abs=1e-9)


def test_ac1_zero_angle():
    approx_list(
        rotated_box_to_corners(RotatedBox(cx=0.5, cy=0.5, w=0.4, h=0.2, theta=0)),
        [0.3, 0.4, 0.7, 0.4, 0.7, 0.6, 0.3, 0.6],
    )


def test_ac2_ninety_degrees():
    approx_list(
        rotated_box_to_corners(RotatedBox(cx=0.5, cy=0.5, w=0.4, h=0.2, theta=90)),
        [0.6, 0.3, 0.6, 0.7, 0.4, 0.7, 0.4, 0.3],
    )


def test_ac3_radians():
    deg = rotated_box_to_corners(RotatedBox(cx=0.5, cy=0.5, w=0.4, h=0.2, theta=90))
    rad = rotated_box_to_corners(RotatedBox(cx=0.5, cy=0.5, w=0.4, h=0.2, theta=math.pi / 2), angle_unit="radians")
    approx_list(rad, deg)


def test_ac4_is_rectangle():
    for theta in (0, 17, 45, 90, 123):
        assert is_rectangle(rotated_box_to_corners(RotatedBox(cx=0.5, cy=0.5, w=0.4, h=0.2, theta=theta)))
    assert not is_rectangle([0.1, 0.1, 0.6, 0.1, 0.7, 0.5, 0.1, 0.5])
    assert not is_rectangle([0.1, 0.1, 0.6, 0.1, 0.1, 0.5])


def test_ac5_aspect_ratio():
    box = RotatedBox(cx=0.5, cy=0.5, w=0.2, h=0.1, theta=45)

    def to_pixels(corners, width, height):
        return [v * (width if i % 2 == 0 else height) for i, v in enumerate(corners)]

    assert is_rectangle(to_pixels(rotated_box_to_corners(box, aspect_ratio=2.0), 200, 100))
    assert not is_rectangle(to_pixels(rotated_box_to_corners(box), 200, 100))


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [({"w": 0}, r"boxes\[0\]\.w"), ({"cx": 1.5}, r"boxes\[0\]\.cx")],
    ids=["zero-width", "cx-out-of-range"],
)
def test_invalid_box_raises(kwargs, match):
    box = RotatedBox(**{"cx": 0.5, "cy": 0.5, "w": 0.4, "h": 0.2, "theta": 0, **kwargs})
    with pytest.raises(ValueError, match=match):
        rotated_box_to_corners(box, name="boxes[0]")


async def test_ac6_tool(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "rotated_bbox_to_polygon",
            {
                "boxes": [
                    {"cx": 0.5, "cy": 0.5, "w": 0.4, "h": 0.2, "theta": 0},
                    {"cx": 0.2, "cy": 0.2, "w": 0.1, "h": 0.1, "theta": 30},
                ]
            },
        )
        polygons = result.structured_content["polygons"]
        assert len(polygons) == 2 and all(len(p) == 8 for p in polygons)
        bad = await client.call_tool(
            "rotated_bbox_to_polygon",
            {"boxes": [{"cx": 0.5, "cy": 0.5, "w": 0, "h": 0.2, "theta": 0}]},
            raise_on_error=False,
        )
    assert bad.is_error and "boxes[0].w" in bad.content[0].text
