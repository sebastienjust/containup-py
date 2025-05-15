#!/usr/bin/env bash

# Script used sometimes, manually to check everything before commit

echo "==> Remove old builds and generated stuff..."
rm -rf dist/ build/ ./*.egg-info
make -C docs clean-docs

echo "==> Format and lint..."
black .
ruff check .
pyright
pytest

echo "==> Build package..."
python -m build

echo "==> Generate documentation..."
make -C docs html