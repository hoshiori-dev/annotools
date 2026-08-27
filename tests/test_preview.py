import io

import pytest
from PIL import Image

from annotools.image.preview import encode, preview
from tests.conftest import make_image


def test_ac1_downscale_fits_limits():
    result = preview(make_image(4000, 3000))
    assert result.image.size == (768, 576)
    assert result.metadata["original_size"] == [4000, 3000]
    assert result.metadata["output_size"] == [768, 576]
    assert result.metadata["scale"] == pytest.approx(768 / 4000)


def test_ac2_no_upscale_by_default():
    assert preview(make_image(400, 300)).image.size == (400, 300)
    assert preview(make_image(400, 300), allow_upscale=True).image.size == (768, 576)


def test_ac3_target_pixels():
    result = preview(make_image(4000, 3000), target_pixels=100_000)
    w, h = result.image.size
    assert w * h <= 100_000 and w <= 768 and h <= 768


def test_ac4_crop_normalized():
    result = preview(make_image(800, 600), crop=(0.25, 0.25, 0.75, 0.75))
    assert result.image.size == (400, 300)
    assert result.metadata["crop"] == [0.25, 0.25, 0.75, 0.75]
    assert result.metadata["scale"] == pytest.approx(1.0)


@pytest.mark.parametrize("crop", [(0.5, 0, 0.5, 1), (0, 0, 1.2, 1)])
def test_ac5_invalid_crop_raises(crop):
    with pytest.raises(ValueError, match="crop"):
        preview(make_image(10, 10), crop=crop)


def test_encode_jpeg_flattens_alpha():
    data = encode(make_image(10, 10, color=(255, 0, 0, 0), mode="RGBA"), "jpeg")
    assert Image.open(io.BytesIO(data)).mode == "RGB"


def test_encode_rejects_unknown_format():
    with pytest.raises(ValueError, match="output_format"):
        encode(make_image(4, 4), "gif")
