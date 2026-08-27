import fsspec
import pytest

from annotools.io import load_image, open_bytes, write_bytes
from tests.conftest import make_image


def test_ac6_fsspec_source(image_file, tmp_path):
    path = image_file(20, 10)
    assert load_image(str(path)).size == (20, 10)
    assert load_image(path.as_uri()).size == (20, 10)
    with fsspec.open("memory://imgs/a.png", "wb") as fh:
        make_image(5, 7).save(fh, format="PNG")
    assert load_image("memory://imgs/a.png").size == (5, 7)
    with pytest.raises(FileNotFoundError, match=r"missing\.png"):
        open_bytes(str(tmp_path / "missing.png"))


def test_write_bytes_roundtrip(tmp_path):
    target = tmp_path / "out" / "x.bin"
    write_bytes(str(target), b"abc")
    assert target.read_bytes() == b"abc"
