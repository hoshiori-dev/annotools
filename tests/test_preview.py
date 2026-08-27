import io

import numpy as np
import pytest
from PIL import Image

from annotools.image.preview import encode, preview
from tests.conftest import make_image


def test_ac1_downscale_fits_limits():
    result = preview(make_image(4000, 3000))
    assert result.image.size == (384, 288)
    assert result.metadata["original_size"] == [4000, 3000]
    assert result.metadata["output_size"] == [384, 288]
    assert (result.metadata["original_width"], result.metadata["original_height"]) == (4000, 3000)
    assert (result.metadata["output_width"], result.metadata["output_height"]) == (384, 288)
    assert result.metadata["scale"] == pytest.approx(384 / 4000)


def test_ac2_no_upscale_by_default():
    assert preview(make_image(300, 200)).image.size == (300, 200)
    assert preview(make_image(300, 200), allow_upscale=True).image.size == (384, 256)
    assert preview(make_image(400, 300), max_width=768, max_height=768, allow_upscale=True).image.size == (768, 576)


def test_ac3_target_pixels():
    result = preview(make_image(4000, 3000), target_pixels=100_000)
    w, h = result.image.size
    assert w * h <= 100_000 and w <= 384 and h <= 384


def test_ac4_crop_normalized():
    result = preview(make_image(800, 600), crop=(0.25, 0.25, 0.75, 0.75), max_width=768, max_height=768)
    assert result.image.size == (400, 300)
    assert result.metadata["crop"] == [0.25, 0.25, 0.75, 0.75]
    assert result.metadata["scale"] == pytest.approx(1.0)


def test_ac4b_crop_reports_applied_box():
    result = preview(make_image(1070, 802), crop=(0.5003, 0.5, 0.5107, 0.51), allow_upscale=True)
    x0, y0, x1, y1 = result.metadata["crop"]
    assert (round(x0 * 1070), round(y0 * 802), round(x1 * 1070), round(y1 * 802)) == (535, 401, 547, 410)
    assert result.metadata["scale"] == pytest.approx(result.image.width / 12)


def test_exif_orientation_applied(tmp_path):
    from PIL import Image as PILImage

    from annotools.io import load_image

    path = tmp_path / "rot.jpg"
    img = make_image(20, 10)
    exif = PILImage.Exif()
    exif[0x0112] = 6  # rotate 90 degrees clockwise on display
    img.save(path, exif=exif)
    assert load_image(str(path)).size == (10, 20)
    assert preview(load_image(str(path))).metadata["original_size"] == [10, 20]


@pytest.mark.parametrize("crop", [(0.5, 0, 0.5, 1), (0, 0, 1.2, 1)])
def test_ac5_invalid_crop_raises(crop):
    with pytest.raises(ValueError, match="crop"):
        preview(make_image(10, 10), crop=crop)


def test_encode_jpeg_flattens_alpha():
    data = encode(make_image(10, 10, color=(255, 0, 0, 0), mode="RGBA"), "jpeg")
    decoded = Image.open(io.BytesIO(data))
    assert decoded.mode == "RGB"
    assert (np.asarray(decoded)[5, 5] > 250).all()  # transparent red flattened onto white


def test_encode_keeps_grayscale():
    data = encode(make_image(10, 10, color=128, mode="L"), "jpeg")
    assert Image.open(io.BytesIO(data)).mode == "L"


def test_encode_rejects_unknown_format():
    with pytest.raises(ValueError, match="output_format"):
        encode(make_image(4, 4), "gif")
