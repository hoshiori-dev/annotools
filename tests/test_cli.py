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


def test_model_level_validation_error_is_reported(capsys):
    with pytest.raises(SystemExit) as exc:
        parse(["--grid-mode", "fixed"])
    assert exc.value.code != 0
    assert "grid_column_width" in capsys.readouterr().err


def test_flag_name_in_error_uses_kebab_case(capsys):
    with pytest.raises(SystemExit):
        parse(["--grid-column-width", "0"])
    assert "--grid-column-width:" in capsys.readouterr().err


@pytest.fixture
def fresh_settings():
    """``main()`` installs settings, which ``configure()`` only allows on an unresolved process."""
    from annotools import config

    config.reset_settings()
    yield
    config.reset_settings()


def _capture_run(monkeypatch):
    import annotools.server as server

    calls: list[dict] = []
    monkeypatch.setattr(server.mcp, "run", lambda **kwargs: calls.append(kwargs))
    return calls


def test_main_runs_stdio_by_default(monkeypatch, fresh_settings):
    from annotools.cli import main

    calls = _capture_run(monkeypatch)
    main([])
    assert calls == [{}]


def test_main_runs_http_with_host_and_port(monkeypatch, fresh_settings):
    from annotools.cli import main

    calls = _capture_run(monkeypatch)
    main(["--http", "--host", "0.0.0.0", "--port", "9000"])
    assert calls == [{"transport": "http", "host": "0.0.0.0", "port": 9000}]


def test_main_installs_the_parsed_settings(monkeypatch, fresh_settings):
    from annotools import config
    from annotools.cli import main

    _capture_run(monkeypatch)
    main(["--max-width", "500"])
    assert config.get_settings().max_width == 500


def test_python_m_annotools_calls_main(monkeypatch):
    import runpy

    seen: list[str] = []
    monkeypatch.setattr("annotools.cli.main", lambda: seen.append("main"))
    runpy.run_module("annotools", run_name="__main__")
    assert seen == ["main"]
