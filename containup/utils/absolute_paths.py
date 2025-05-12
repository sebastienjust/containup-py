from pathlib import Path
import sys


def to_absolute_path(path: str) -> str:
    """
    If the given path is relative, convert it to an absolute path
    based on the directory where the main script was launched.
    If it's already absolute, return it unchanged.
    """
    p = Path(path)
    if p.is_absolute():
        return str(p)
    base_path = Path(sys.argv[0]).resolve().parent
    return str((base_path / p).resolve())
