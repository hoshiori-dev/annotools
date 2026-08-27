import pytest

from annotools.cli import build_parser, parse


def test_defaults_to_stdio():
    args, settings = parse([])
    assert args.http is False
    assert args.port == 8000
    assert settings.max_width == 384


def test_http_flags():
    args, _ = parse(["--http", "--host", "0.0.0.0", "--port", "9000"])
    assert args.http is True
    assert (args.host, args.port) == ("0.0.0.0", 9000)


def test_help_mentions_transports(capsys):
    parser, _ = build_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "--http" in out
    assert "stdio" in out


def test_help_lists_settings_flags(capsys):
    parser, _ = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--help"])
    out = capsys.readouterr().out
    assert "--max-width" in out and "--grid-columns" in out
    assert "ANNOTOOLS_MAX_WIDTH" in out


def test_settings_flags_override_env(monkeypatch):
    monkeypatch.setenv("ANNOTOOLS_MAX_WIDTH", "700")
    _, from_env = parse([])
    assert from_env.max_width == 700
    _, from_flag = parse(["--max-width", "500", "--grid-columns", "8"])
    assert from_flag.max_width == 500 and from_flag.grid_columns == 8


def test_invalid_flag_value_exits(capsys):
    with pytest.raises(SystemExit) as exc:
        parse(["--max-width", "0"])
    assert exc.value.code != 0
