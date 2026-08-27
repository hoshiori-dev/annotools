import pytest
from fastmcp import Client

from annotools.geometry import denormalize_coordinates, normalize_coordinates


def approx_lists(values, expected):
    assert len(values) == len(expected)
    for got, want in zip(values, expected, strict=True):
        assert got == pytest.approx(want, abs=1e-9)


def test_ac1_pixel_base_normalizes():
    approx_lists(normalize_coordinates([[192, 144]], 384, 288), [[0.5, 0.5]])
    approx_lists(normalize_coordinates([[0, 0, 384, 288], [96, 72]], 384, 288), [[0, 0, 1, 1], [0.25, 0.25]])


def test_ac2_crop_maps_into_source():
    out = normalize_coordinates([[0, 0, 400, 300]], 400, 300, crop=(0.25, 0.25, 0.75, 0.75))
    approx_lists(out, [[0.25, 0.25, 0.75, 0.75]])


def test_ac3_round_trip():
    crop = (0.1, 0.2, 0.9, 0.7)
    boxes = [[0.15, 0.25, 0.5, 0.6], [0.3, 0.3]]
    thousand = denormalize_coordinates(boxes, 1000, 1000, crop=crop)
    approx_lists(normalize_coordinates(thousand, 1000, 1000, crop=crop), boxes)


def test_ac4_yx_order():
    approx_lists(normalize_coordinates([[100, 200, 300, 400]], 1000, 1000, axis_order="yx"), [[0.2, 0.1, 0.4, 0.3]])
    approx_lists(denormalize_coordinates([[0.2, 0.1, 0.4, 0.3]], 1000, 1000, axis_order="yx"), [[100, 200, 300, 400]])


def test_ac5_clamps_out_of_range():
    approx_lists(normalize_coordinates([[-5, 999]], 384, 384), [[0, 1]])


def test_ac6_odd_length_raises():
    with pytest.raises(ValueError, match=r"coordinates\[1\]: expected an even number"):
        normalize_coordinates([[1, 2], [1, 2, 3]], 10, 10)


def test_ac7_bad_base_raises():
    with pytest.raises(ValueError, match="base_width"):
        normalize_coordinates([[1, 2]], 0, 10)
    with pytest.raises(ValueError, match="crop"):
        denormalize_coordinates([[0.5, 0.5]], 10, 10, crop=(0.5, 0.5, 0.2, 0.9))


def test_ac8_denormalize_rejects_out_of_range():
    with pytest.raises(ValueError, match=r"coordinates\[0\].*outside"):
        denormalize_coordinates([[1.2, 0.5]], 10, 10)


def test_denormalize_outside_crop_is_not_clamped():
    approx_lists(denormalize_coordinates([[0.0, 0.0]], 100, 100, crop=(0.5, 0.5, 1, 1)), [[-100, -100]])


async def test_ac9_tools(mcp_server):
    async with Client(mcp_server) as client:
        pixels = await client.call_tool(
            "normalize_coordinates", {"coordinates": [[192, 144, 384, 288]], "base_width": 384, "base_height": 288}
        )
        gpt = await client.call_tool(
            "normalize_coordinates", {"coordinates": [[0, 0, 999, 999]], "base_width": 999, "base_height": 999}
        )
        back = await client.call_tool(
            "denormalize_coordinates",
            {"coordinates": [[0.5, 0.5, 1, 1]], "base_width": 1000, "base_height": 1000, "axis_order": "yx"},
        )
        bad = await client.call_tool(
            "normalize_coordinates",
            {"coordinates": [[1, 2, 3]], "base_width": 10, "base_height": 10},
            raise_on_error=False,
        )
    approx_lists(pixels.structured_content["coordinates"], [[0.5, 0.5, 1, 1]])
    approx_lists(gpt.structured_content["coordinates"], [[0, 0, 1, 1]])
    approx_lists(back.structured_content["coordinates"], [[500, 500, 1000, 1000]])
    assert bad.is_error and "coordinates[0]" in bad.content[0].text
