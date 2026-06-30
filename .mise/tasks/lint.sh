#!/usr/bin/env bash
#MISE description="Lint all code"
set -euo pipefail
uv sync --frozen 2>/dev/null || uv sync
uv run ruff format --check .
uv run ruff check .
