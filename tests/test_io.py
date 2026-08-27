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
    with pytest.raises(OSError, match=str(tmp_path)) as info:
        open_bytes(str(tmp_path))
    assert type(info.value) is OSError
    (tmp_path / "text.txt").write_text("not an image")
    with pytest.raises(ValueError, match=r"text\.txt"):
        load_image(str(tmp_path / "text.txt"))


def test_unknown_protocol_and_backend_errors_name_the_uri(monkeypatch):
    with pytest.raises(OSError, match=r"zzz://bucket/a\.png") as info:
        open_bytes("zzz://bucket/a.png")
    assert type(info.value) is OSError

    class BoomError(Exception):
        pass

    def explode(*args, **kwargs):
        raise BoomError("Unable to locate credentials")

    monkeypatch.setattr(fsspec, "open", explode)
    with pytest.raises(OSError, match=r"s3://bucket/a\.png.*credentials"):
        open_bytes("s3://bucket/a.png")


def test_truncated_image_raises_value_error(tmp_path):
    path = tmp_path / "trunc.png"
    make_image(64, 64).save(path)
    path.write_bytes(path.read_bytes()[:-40])
    with pytest.raises(ValueError, match=r"trunc\.png"):
        load_image(str(path))


def test_write_bytes_error_names_target():
    with pytest.raises(OSError, match=r"zzz://x/y\.bin"):
        write_bytes("zzz://x/y.bin", b"abc")


def test_write_bytes_roundtrip(tmp_path):
    target = tmp_path / "out" / "x.bin"
    write_bytes(str(target), b"abc")
    assert target.read_bytes() == b"abc"
