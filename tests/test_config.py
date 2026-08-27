import pytest
from pydantic import ValidationError

from annotools import config
from annotools.config import Settings


def test_defaults():
    s = Settings()
    assert (s.max_width, s.max_height, s.target_pixels) == (384, 384, None)
    assert (s.grid_columns, s.grid_rows, s.grid_mode) == (10, 10, "ratio")
    assert (s.grid_column_width, s.grid_row_width) == (None, None)
    assert (s.line_width, s.point_diameter, s.color, s.output_format, s.jpeg_quality) == (2, 3, "blue", "jpeg", 90)


def test_env_override_and_empty_ignored(monkeypatch):
    monkeypatch.setenv("ANNOTOOLS_MAX_WIDTH", "700")
    monkeypatch.setenv("ANNOTOOLS_GRID_ROWS", "4")
    assert Settings().max_width == 700 and Settings().grid_rows == 4
    monkeypatch.setenv("ANNOTOOLS_MAX_WIDTH", "")
    assert Settings().max_width == 384


def test_invalid_env_raises(monkeypatch):
    monkeypatch.setenv("ANNOTOOLS_MAX_WIDTH", "0")
    with pytest.raises(ValidationError, match="max_width"):
        Settings()


def test_fixed_mode_requires_widths():
    with pytest.raises(ValidationError, match="grid_column_width"):
        Settings(grid_mode="fixed")
    assert Settings(grid_mode="fixed", grid_column_width=100, grid_row_width=50).grid_row_width == 50


def test_configure_after_resolution_raises():
    config.get_settings()
    with pytest.raises(RuntimeError, match="configure"):
        config.configure(Settings())


def test_configure_before_resolution(monkeypatch):
    monkeypatch.setattr(config, "_settings", None)
    config.configure(Settings(max_width=512))
    assert config.get_settings().max_width == 512
    config.reset_settings()
    assert config.get_settings().max_width == 384
