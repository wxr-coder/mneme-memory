#!/usr/bin/env bash
#MISE description="First-time setup wizard"
set -euo pipefail

echo "=== mneme-memory setup ==="
echo ""

# Check mise
if ! command -v mise &>/dev/null; then
    echo "ERROR: mise is not installed. Install from https://mise.run"
    exit 1
fi

# Install tools
echo "Installing tools from .mise/config.toml..."
mise install

# Trust config
mise trust -y . 2>/dev/null || true

# Sync dependencies
echo "Syncing Python dependencies..."
uv sync

# Install pre-commit hooks
if command -v prek &>/dev/null; then
    echo "Installing git hooks..."
    prek install --config prek.toml 2>/dev/null || true
elif command -v uvx &>/dev/null; then
    echo "Installing git hooks via uvx..."
    uvx prek install --config prek.toml 2>/dev/null || true
fi

echo ""
echo "=== Setup complete! ==="
echo "Run: mise run test    # Run tests"
echo "Run: uv run mneme     # CLI tool"
echo "Run: uv run mneme-server  # Start server"
