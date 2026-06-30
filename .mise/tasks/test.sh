#!/usr/bin/env bash
#MISE description="Quick tests (skip live_llm marker)"
set -euo pipefail
uv sync --frozen 2>/dev/null || uv sync
uv run pytest -n auto -m "not live_llm" --cov=packages --cov=apps --cov=demos --cov-report=term:skip-covered
