"""Shared utility functions for bundium.

Deprecated: Path exclusion logic inlined into indexer.py.
"""

from pathlib import Path


def is_excluded_path(path: Path) -> bool:
    """True when any part is hidden or a cache dir."""
    return any(part.startswith(".") for part in path.parts) or (
        "__pycache__" in path.parts
    )
