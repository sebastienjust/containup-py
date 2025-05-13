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

echo "==> Tag Git and push if successful..."
git tag "$version" -m "Release $version"
git push origin "$release_branch"
git push origin "$version"


echo "==> Ready to publish. If successful Prêt à publier. Utilise la commande suivante si tout est OK :"
echo "twine upload --repository testpypi dist/*"
echo "twine upload dist/*"
