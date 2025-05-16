#!/usr/bin/env python3

import shutil
import toml
import json
from pathlib import Path


def main():
    """Generate a project context in docs as a project summary."""

    root = Path(__file__).resolve().parent
    target = root / "docs" / "build" / "containup-context"
    target.mkdir(exist_ok=True)

    files = [
        "pyproject.toml",
        "requirements-dev.txt",
        "pyrightconfig.json",
        "README.md",
        "docs/build/text/api.txt",
        "release.sh",
    ]

    for relative_path in files:
        src = root / relative_path
        if src.exists():
            dest = target / src.name
            shutil.copy(src, dest)

    pyproject = toml.load(root / "pyproject.toml")
    pyright = json.load(open(root / "pyrightconfig.json"))
    dev_deps = (root / "requirements-dev.txt").read_text().splitlines()

    context = {
        "name": pyproject["project"]["name"],
        "version": pyproject["project"]["version"],
        "python": pyproject["project"]["requires-python"],
        "description": pyproject["project"]["description"],
        "license": pyproject["project"]["license"],
        "core_deps": pyproject["project"].get("dependencies", []),
        "dev_deps": dev_deps,
        "type_checking": pyright.get("typeCheckingMode"),
        "tools": list(pyproject.get("tool", {}).keys()),
        "entry": "containup",
        "notes": "Projet en développement actif. API instable.",
    }

    with open(target / ".project-context", "w") as f:
        for k, v in context.items():
            f.write(f"{k} = {v!r}\n")


if __name__ == "__main__":
    main()
