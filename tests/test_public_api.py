import importlib
import subprocess
import sys

import pytest

import annotools

LIBRARY_MODULES = (
    "annotools.config",
    "annotools.io",
    "annotools.color",
    "annotools.geometry",
    "annotools.image.preview",
    "annotools.image.grid",
    "annotools.image.overlay",
    "annotools.image.segmentation",
    "annotools.video",
    "annotools.audio",
)


def test_every_facade_name_resolves():
    for name in annotools.__all__:
        assert getattr(annotools, name) is not None, name


def test_facade_is_the_union_of_the_module_exports():
    exported = {"__version__"}
    for module in LIBRARY_MODULES:
        exported.update(importlib.import_module(module).__all__)
    assert set(annotools.__all__) == exported
    assert len(annotools.__all__) == len(set(annotools.__all__))


@pytest.mark.parametrize("module", LIBRARY_MODULES)
def test_module_exports_exist_and_are_public_names(module):
    mod = importlib.import_module(module)
    for name in mod.__all__:
        assert not name.startswith("_") and hasattr(mod, name), (module, name)


def test_importing_the_facade_loads_neither_fastmcp_nor_the_mcp_package():
    code = "import sys, annotools; print('fastmcp' in sys.modules, 'annotools.mcp' in sys.modules)"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["False", "False"]


def test_facade_works_without_the_media_extra(monkeypatch):
    """``av`` is imported lazily, so the facade imports even when PyAV is missing."""
    code = "import sys; sys.modules['av'] = None; import annotools; print(annotools.clip_audio.__name__)"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "clip_audio"
