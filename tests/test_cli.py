import pytest

from annotools.cli import build_parser


def test_defaults_to_stdio():
    args = build_parser().parse_args([])
    assert args.http is False
    assert args.port == 8000


def test_http_flags():
    args = build_parser().parse_args(["--http", "--host", "0.0.0.0", "--port", "9000"])
    assert args.http is True
    assert (args.host, args.port) == ("0.0.0.0", 9000)


def test_help_mentions_transports(capsys):
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "--http" in out
    assert "stdio" in out
