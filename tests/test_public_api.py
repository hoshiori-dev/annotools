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


INTERNAL_NAMES = {
    "annotools.image.preview": ("size_metadata", "FORMATS"),
    "annotools.image.overlay": ("_Mapper", "_validate_polygon"),
    "annotools.image.grid": ("_line_positions",),
    "annotools.color": ("text_color_for",),
    "annotools.geometry": ("normalized_box_to_pixels",),
}


@pytest.mark.parametrize(("module", "names"), INTERNAL_NAMES.items(), ids=list(INTERNAL_NAMES))
def test_internal_names_stay_out_of_the_public_api(module, names):
    exported = importlib.import_module(module).__all__
    for name in names:
        assert name not in exported and name not in annotools.__all__, (module, name)


def test_every_library_module_is_listed():
    """A new library module with an ``__all__`` must be added to LIBRARY_MODULES (and the facade)."""
    import pkgutil

    found = set()
    for info in pkgutil.walk_packages(annotools.__path__, prefix="annotools."):
        if info.name.startswith("annotools.mcp") or info.name.rsplit(".", 1)[-1].startswith("_"):
            continue
        if hasattr(importlib.import_module(info.name), "__all__"):
            found.add(info.name)
    assert found == set(LIBRARY_MODULES)


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
