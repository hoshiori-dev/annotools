import json

import numpy as np
import pytest
from fastmcp import Client
from PIL import Image

from annotools.color import color_from_text
from annotools.image.grid import GridOptions
from annotools.image.preview import preview
from annotools.image.segmentation import load_mask, overlay_mask
from tests.conftest import make_image


def mask_array(width=200, height=100):
    m = np.zeros((height, width), dtype=np.uint8)
    m[10:50, 10:90] = 1
    m[60:90, 120:190] = 2
    return m


def pix(image, x, y):
    return tuple(int(v) for v in np.asarray(image.convert("RGB"))[y, x])


def blend(color, alpha=0.5):
    return tuple(round(255 * (1 - alpha) + c * alpha) for c in color)


def test_ac1_mask_colours_regions():
    result = overlay_mask(preview(make_image(200, 100)), mask_array(), annotation="legend", line_width=0)
    img = result.image
    assert pix(img, 15, 15) == blend(color_from_text("1"))  # away from the label/legend
    assert pix(img, 125, 65) == blend(color_from_text("2"))
    assert pix(img, 5, 5) == (255, 255, 255)
    assert result.metadata["ids"] == 2


def test_ac2_mask_resized_to_source():
    small = mask_array()[::2, ::2]  # 100x50 mask for a 200x100 image
    img = overlay_mask(preview(make_image(200, 100)), small, annotation="legend", line_width=0).image
    assert pix(img, 15, 15) == blend(color_from_text("1"))
    assert pix(img, 100, 30) == (255, 255, 255)


def test_ac3_label_mode_draws_ids():
    plain = np.asarray(
        overlay_mask(preview(make_image(200, 100)), mask_array(), annotation="legend", line_width=0).image.convert(
            "RGB"
        )
    )[:100]
    numbered = np.asarray(
        overlay_mask(preview(make_image(200, 100)), mask_array(), annotation="label", line_width=0).image.convert("RGB")
    )
    named = np.asarray(
        overlay_mask(
            preview(make_image(200, 100)), mask_array(), annotation="label", id_names={1: "cat"}, line_width=0
        ).image.convert("RGB")
    )
    assert (plain[20:40, 35:65] != numbered[20:40, 35:65]).any()  # region 1 centroid ~ (50, 30)
    assert (numbered != named).any()


def test_ac4_legend_mode_fits_limits():
    result = overlay_mask(
        preview(make_image(200, 100), max_height=110),
        mask_array(),
        annotation="legend",
        id_names={2: "dog"},
        max_height=110,
    )
    assert result.image.height <= 110
    assert result.metadata["legend"] == [
        {"id": 1, "name": "1", "color": "#{:02x}{:02x}{:02x}".format(*color_from_text("1"))},
        {"id": 2, "name": "dog", "color": "#{:02x}{:02x}{:02x}".format(*color_from_text("2"))},
    ]


def test_ac5_non_single_channel_raises(tmp_path):
    path = tmp_path / "rgb.png"
    Image.new("RGB", (10, 10), "red").save(path)
    with pytest.raises(ValueError, match="mask_source"):
        load_mask(str(path))


def test_load_mask_accepts_uint16(tmp_path):
    path = tmp_path / "m16.png"
    Image.fromarray(mask_array().astype(np.uint16) * 300).save(path)
    m = load_mask(str(path))
    assert m.shape == (100, 200) and int(m.max()) == 600


def test_outline_and_invalid_params():
    result = overlay_mask(preview(make_image(200, 100)), mask_array(), line_width=2)
    assert pix(result.image, 10, 30) == color_from_text("1")  # boundary pixel at full opacity
    with pytest.raises(ValueError, match="alpha"):
        overlay_mask(preview(make_image(20, 10)), mask_array(20, 10), alpha=1.5)
    with pytest.raises(ValueError, match="annotation"):
        overlay_mask(preview(make_image(20, 10)), mask_array(20, 10), annotation="none")


async def test_ac6_tool(mcp_server, image_file, tmp_path):
    mask_path = tmp_path / "mask.png"
    Image.fromarray(mask_array(400, 200)).save(mask_path)
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "preview_image_segmentation",
            {"source": str(image_file(400, 200)), "mask_source": str(mask_path), "grid": {"columns": 4, "rows": 2}},
        )
    meta = json.loads(result.content[1].text)
    assert meta["ids"] == 2 and meta["grid"]["columns"] == 4
    assert GridOptions(columns=4).columns == 4


def test_ac7_crop_alignment():
    # a crop that does not fall on pixel boundaries: mask rows must cover exactly the image rows
    source = make_image(527, 757)
    mask = np.zeros((757, 527), dtype=np.uint8)
    mask[347:472, 121:215] = 1  # the pixel box the image crop will receive
    result = preview(source, crop=(0.23087, 0.45960, 0.40695, 0.62330))
    assert result.crop_pixels == (121, 347, 215, 472)
    out = overlay_mask(result, mask, annotation="legend", line_width=0)
    top = np.asarray(out.image.convert("RGB"))[: result.image.height]
    assert (top != 255).all(axis=-1).all()  # every image pixel is coloured, including the last row/col


def test_ac8_line_width():
    result = overlay_mask(preview(make_image(200, 100)), mask_array(), annotation="legend", line_width=0)
    assert pix(result.image, 10, 30) == blend(color_from_text("1"))  # boundary pixel blended, not solid
    with pytest.raises(ValueError, match="line_width"):
        overlay_mask(preview(make_image(20, 10)), mask_array(20, 10), line_width=-1)


def test_ac9_legend_metadata():
    result = overlay_mask(
        preview(make_image(400, 200), max_height=100), mask_array(400, 200), annotation="legend", max_height=100
    )
    image_w, image_h = result.metadata["image_size"]
    assert result.image.height <= 100 and result.metadata["output_size"][1] <= 100
    assert (
        result.metadata["output_width"] == result.image.width
        and result.metadata["output_height"] == result.image.height
    )
    assert image_h < result.image.height
    assert result.metadata["scale"] == pytest.approx(image_w / 400, abs=0.01)


def test_rgba_source_flattened_on_white():
    rgba = Image.new("RGBA", (20, 10), (255, 0, 0, 0))
    out = overlay_mask(preview(rgba), np.zeros((10, 20), dtype=np.uint8), annotation="legend")
    assert pix(out.image, 5, 5) == (255, 255, 255)


async def test_string_keyed_id_names(mcp_server, image_file, tmp_path):
    mask_path = tmp_path / "mask.png"
    Image.fromarray(mask_array(400, 200)).save(mask_path)
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "preview_image_segmentation",
            {
                "source": str(image_file(400, 200)),
                "mask_source": str(mask_path),
                "annotation": "legend",
                "id_names": {"1": "cat"},
                "max_width": 768,
                "max_height": 768,
            },
        )
    meta = json.loads(result.content[1].text)
    assert meta["legend"][0]["name"] == "cat" and meta["image_size"] == [400, 200]
