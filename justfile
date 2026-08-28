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
    uv run pytest -m "not container" --cov --cov-report=term --cov-report=xml

# Container smoke tests; needs a docker daemon and `just docker-build`
test-container:
    uv run pytest -m container

# Check that every label referenced by forms/release.yml exists in .github/labels.json
check-taxonomy:
    uv run --with pyyaml==6.0.2 scripts/check_taxonomy.py --labels .github/labels.json

# Show the label sync plan (dry run); apply with `just sync-labels --apply`
sync-labels *args:
    uv run scripts/sync_labels.py --repo hoshiori-dev/annotools --file .github/labels.json {{args}}

# Check README.md and README.zh.md share the same structure
readme-check:
    uv run scripts/check_readme_sync.py

# Everything CI runs on a pull request (except container tests)
check: lint format-check typecheck check-taxonomy readme-check check-docs docs-check test-cov

# Regenerate docs/mcp/tools.md from the running MCP server
docs-gen:
    uv run scripts/gen_mcp_reference.py

# Build the documentation site (regenerates the tool reference first)
docs: docs-gen
    uv run zensical build --clean

# Every public name has a complete Google docstring
check-docs:
    uv run scripts/check_public_docstrings.py

# Check the generated tool reference is current, then build strictly (warnings fail), as CI does
docs-check:
    uv run scripts/gen_mcp_reference.py --check
    uv run zensical build --clean --strict

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
