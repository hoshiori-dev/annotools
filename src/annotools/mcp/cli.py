"""Command-line entrypoint for the annotools MCP server."""

import argparse
from collections.abc import Sequence

from pydantic import ValidationError
from pydantic_core import ErrorDetails
from pydantic_settings import CliSettingsSource

from annotools import __version__, config
from annotools.config import Settings


def build_parser() -> tuple[argparse.ArgumentParser, CliSettingsSource[Settings]]:
    """Build the argument parser for the ``annotools`` command and the settings source attached to it."""
    parser = argparse.ArgumentParser(
        prog="annotools",
        description="Run the annotools MCP server. Preview defaults can be set by flag or ANNOTOOLS_* variable.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--http", action="store_true", help="serve over HTTP instead of stdio (default: stdio)")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="HTTP port (default: 8000)")
    source = CliSettingsSource(
        Settings, root_parser=parser, cli_parse_args=False, cli_kebab_case=True, cli_show_env_vars=True
    )
    return parser, source


def parse(argv: Sequence[str] | None = None) -> tuple[argparse.Namespace, Settings]:
    """Parse ``argv`` into transport options and the resolved settings (flags > environment > defaults)."""
    parser, source = build_parser()
    args = parser.parse_args(argv)
    try:
        settings = Settings(_cli_settings_source=source(parsed_args=args))
    except ValidationError as exc:
        parser.error("; ".join(_describe(error) for error in exc.errors()))
    return args, settings


def _describe(error: ErrorDetails) -> str:
    """Render one pydantic error as ``--flag: message`` (model-level errors have no field)."""
    loc = error.get("loc") or ()
    message = error["msg"].removeprefix("Value error, ")
    return f"--{str(loc[0]).replace('_', '-')}: {message}" if loc else message


def main(argv: Sequence[str] | None = None) -> None:
    """Parse arguments, install the settings, and run the server."""
    args, settings = parse(argv)
    config.configure(settings)
    # Deferred so that --help and --version stay fast, and so tool defaults see the configured settings.
    from annotools.mcp.server import mcp

    if args.http:
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run()
