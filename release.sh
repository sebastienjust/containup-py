#!/bin/bash
set -e

echo "==> Bump version number"
bumpver update --patch

echo "==> Remove old builds..."
rm -rf dist/ build/ *.egg-info

echo "==> Formatat and lint..."
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
version=$(bumpver show | grep "Current Version" | awk '{print $NF}')
git tag "$version" -m "Release $version"
git push origin "$version"

echo "==> Ready to publish. If successful Prêt à publier. Utilise la commande suivante si tout est OK :"
echo "twine upload --repository testpypi dist/*"
echo "twine upload dist/*"
