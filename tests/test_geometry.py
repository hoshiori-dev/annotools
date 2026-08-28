import pytest

from annotools.geometry import (
    fit_size,
    is_rectangle,
    normalized_box_to_pixels,
    validate_normalized_box,
    validate_normalized_point,
)


@pytest.mark.parametrize(
    ("size", "limits", "expected"),
    [
        ((4000, 3000), (768, 768), (768, 576)),
        ((3000, 4000), (768, 768), (576, 768)),
        ((400, 300), (768, 768), (400, 300)),
        ((1000, 1000), (768, 384), (384, 384)),
    ],
    ids=["landscape", "portrait", "already-small", "height-bound"],
)
def test_fit_size_downscales_only(size, limits, expected):
    assert fit_size(*size, max_width=limits[0], max_height=limits[1]) == expected


def test_fit_size_upscale_when_allowed():
    assert fit_size(400, 300, max_width=768, max_height=768, allow_upscale=True) == (768, 576)


def test_fit_size_target_pixels_caps_area():
    w, h = fit_size(4000, 3000, max_width=768, max_height=768, target_pixels=100_000)
    assert w * h <= 100_000
    assert w <= 768 and h <= 768
    assert abs(w / h - 4 / 3) < 0.02


@pytest.mark.parametrize("box", [(0.5, 0.0, 0.5, 1.0), (0.0, 0.0, 1.2, 1.0), (-0.1, 0.0, 0.5, 0.5)])
def test_validate_box_rejects_bad_values(box):
    with pytest.raises(ValueError, match="crop"):
        validate_normalized_box(box, name="crop")


def test_box_to_pixels_rounds_outward():
    assert normalized_box_to_pixels((0.25, 0.25, 0.75, 0.75), 800, 600) == (200, 150, 600, 450)
    assert normalized_box_to_pixels((0.001, 0.001, 0.999, 0.999), 100, 100) == (0, 0, 100, 100)


@pytest.mark.parametrize("width", range(769, 4608, 37))
def test_fit_size_hits_limit_exactly(width):
    w, h = fit_size(width, 384, max_width=768, max_height=768)
    assert w == 768 and h == round(384 * 768 / width)


def test_fit_size_never_exceeds_target_pixels():
    for width, height in ((1023, 767), (999, 1001), (4000, 3000)):
        w, h = fit_size(width, height, max_width=10_000, max_height=10_000, target_pixels=250_000)
        assert w * h <= 250_000


@pytest.mark.parametrize(
    ("validator", "value", "match"),
    [
        (validate_normalized_box, (0.0, 0.0, 1.0), r"field: expected 4 values"),
        (validate_normalized_point, (0.5,), r"field: expected 2 values"),
    ],
    ids=["box", "point"],
)
def test_wrong_length_names_the_field(validator, value, match):
    with pytest.raises(ValueError, match=match):
        validator(value, name="field")


@pytest.mark.parametrize(
    "kwargs",
    [{"max_width": 0, "max_height": 10}, {"max_width": 10, "max_height": 10, "target_pixels": 0}],
    ids=["max-size", "target-pixels"],
)
def test_fit_size_rejects_limits_below_one(kwargs):
    with pytest.raises(ValueError, match=">= 1"):
        fit_size(100, 100, **kwargs)


def test_is_rectangle_rejects_zero_length_edge():
    assert is_rectangle([0, 0, 0, 0, 1, 1, 1, 0]) is False
