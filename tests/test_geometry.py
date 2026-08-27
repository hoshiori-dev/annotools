import pytest

from annotools.geometry import fit_size, normalized_box_to_pixels, validate_normalized_box


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
