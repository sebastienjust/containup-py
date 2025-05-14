#!/usr/bin/env bash
echo "==> Cleanup files like __pycache__..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete
rm -rf dist/ build/ *.egg-info .ruff_cache/ .pytest_cache/
rm -rf .ruff_cache
make -C docs clean-docs