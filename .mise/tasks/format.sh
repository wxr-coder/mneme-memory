#!/usr/bin/env bash
#MISE description="Format all code"
set -euo pipefail
uv sync --frozen 2>/dev/null || uv sync
uv run ruff format .
uv run ruff check . --fix
