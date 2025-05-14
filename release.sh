#!/bin/bash
set -e

echo "==> Create temp branch for release..."
git checkout -b release-temp

echo "==> Bump version number"
bumpver update --patch

echo "==> Gets new version number"
version=$(bumpver show | grep "Current Version" | awk '{print $NF}')
release_branch="release/$version"

echo "==> Rename temporary branch : $release_branch"
git branch -m "$release_branch"

echo "==> Remove old builds..."
rm -rf dist/ build/ ./*.egg-info

echo "==> Format and lint..."
black .
ruff check .
pyright

echo "==> Tests..."
pytest

echo "==> Build package..."
python -m build

echo "==> Chack with twine..."
twine check dist/*

echo "==> Generate documentation..."
make -C docs clean-docs
make -C docs html

echo "==> Push branch if successful..."
git push origin "$release_branch"

echo "==> Ready to publish. "
echo "If successful go to GitHub, create PR, merge and do a release. "
echo "GitHub actions will publish on PyPI"


