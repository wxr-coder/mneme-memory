#!/usr/bin/env bash
#MISE description="Full test suite"
set -euo pipefail
uv sync --frozen 2>/dev/null || uv sync
uv run pytest -n auto --cov=packages --cov=apps --cov=demos --cov-report=term:skip-covered
