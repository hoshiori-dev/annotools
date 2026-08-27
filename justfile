# Task entrypoints. Agents and CI run `just check`; humans iterate on the parts.

set shell := ["bash", "-euo", "pipefail", "-c"]

image := "annotools:dev"

default:
    @just --list

# Install the project with dev dependencies
sync:
    uv sync --all-extras

# Lint with ruff (no fixes)
lint:
    uv run ruff check .

# Fix lint findings and format
fix:
    uv run ruff check --fix .
    uv run ruff format .

# Verify formatting without changing files
format-check:
    uv run ruff format --check .

# Static type check
typecheck:
    uv run ty check

# Unit tests (container tests are deselected)
test *args:
    uv run pytest -m "not container" {{args}}

# Unit tests with coverage report
test-cov:
    uv run pytest -m "not container" --cov --cov-report=term

# Container smoke tests; needs a docker daemon and `just docker-build`
test-container:
    uv run pytest -m container

# Everything CI runs on a pull request (except container tests)
check: lint format-check typecheck test

# Build the documentation site
docs:
    uv run zensical build --clean

# Serve the documentation locally
docs-serve:
    uv run zensical serve

# Run the MCP server over stdio
mcp:
    uv run annotools

# Run the MCP server over HTTP for interactive debugging
mcp-http port="8000":
    uv run annotools --http --port {{port}}

# Build the container image
docker-build tag=image:
    docker build -t {{tag}} .

# Print the container's CLI usage
docker-run tag=image *args="--help":
    docker run --rm {{tag}} {{args}}
