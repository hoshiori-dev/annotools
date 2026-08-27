"""Command-line entrypoint that starts the MCP server."""

import argparse
from collections.abc import Sequence

from annotools import __version__


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the ``annotools`` command."""
    parser = argparse.ArgumentParser(prog="annotools", description="Run the annotools MCP server.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--http", action="store_true", help="serve over HTTP instead of stdio (default: stdio)")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="HTTP port (default: 8000)")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Parse arguments and run the server."""
    args = build_parser().parse_args(argv)
    # Deferred so that --help and --version stay fast.
    from annotools.server import mcp

    if args.http:
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run()
