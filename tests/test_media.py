import sys
from contextlib import ExitStack

import pytest

from annotools._media import open_container, require_av


def test_require_av_names_the_extra(monkeypatch):
    monkeypatch.setitem(sys.modules, "av", None)
    with pytest.raises(ImportError, match=r"audio support requires PyAV: install annotools\[media\]"):
        require_av("audio")


def test_require_av_returns_the_module():
    assert require_av("video").__name__ == "av"


@pytest.mark.parametrize(
    ("uri", "error", "match"),
    [
        ("nope://x.mp4", OSError, r"cannot read nope://x\.mp4"),
        ("/definitely/missing.mp4", FileNotFoundError, r"missing\.mp4"),
    ],
    ids=["unknown-protocol", "missing-file"],
)
def test_open_container_errors_name_the_uri(uri, error, match):
    with pytest.raises(error, match=match), ExitStack() as stack:
        open_container(require_av("video"), uri, stack)


def test_open_container_rejects_non_media(tmp_path):
    junk = tmp_path / "junk.bin"
    junk.write_bytes(bytes(range(256)) * 64)
    with pytest.raises(ValueError, match=r"junk\.bin"), ExitStack() as stack:
        open_container(require_av("video"), str(junk), stack)
