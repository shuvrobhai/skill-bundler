"""Core domain logic for bundling a skill directory into a Markdown document."""

import os
import re
from pathlib import Path

from bundium.bundle_format import serialize
from bundium.frontmatter import parse_skill_text


def collect_skill_files(skill_dir: Path) -> list[Path]:
    """Return all non-hidden, non-symlink files except the root SKILL.md."""
    files = []
    root_skill_md = (skill_dir / "SKILL.md").resolve()

    for root, dirnames, filenames in os.walk(skill_dir):
        # Prune hidden directories and __pycache__ from descending
        dirnames[:] = [
            d for d in sorted(dirnames)
            if not d.startswith(".") and d != "__pycache__" and not (Path(root) / d).is_symlink()
        ]

        for fname in sorted(filenames):
            if fname.startswith("."):
                continue
            path = Path(root) / fname
            if path.is_symlink():
                continue
            if path.resolve() == root_skill_md:
                continue

            files.append(path)

    files.sort()
    return files


def _structure_map_sort_key(path: Path):
    """SKILL.md first, then directories, then other files."""
    if path.name == "SKILL.md":
        return (0, 0, "")
    if path.is_dir():
        return (0, 1, path.name.lower())
    return (1, 0, path.name.lower())


def _render_structure_map_body(directory: Path, prefix: str, lines: list[str]) -> None:
    entries = sorted(
        [
            p
            for p in directory.iterdir()
            if not p.name.startswith(".")
            and p.name != "__pycache__"
            and not p.is_symlink()
        ],
        key=_structure_map_sort_key,
    )

    for i, path in enumerate(entries):
        is_last = i == len(entries) - 1
        connector = "└── " if is_last else "├── "
        lines.append(prefix + connector + path.name)

        if path.is_dir():
            child_prefix = "    " if is_last else "│   "
            _render_structure_map_body(path, prefix + child_prefix, lines)


def build_structure_map(skill_dir: Path) -> str:
    """Return a text tree representation (Structure Map) of the skill directory."""
    lines = [skill_dir.name]
    _render_structure_map_body(skill_dir, "", lines)
    return "\n".join(lines)


def build_bundle_document(
    skill_dir: Path, skill_md_path: Path, files: list[Path]
) -> tuple[str, int, list[str]]:
    """Build one Markdown document with metadata, structure map, and inlined files."""
    skill_text = skill_md_path.read_text(encoding="utf-8")
    name, description, body = parse_skill_text(skill_text)
    title = name or skill_dir.name
    uri = skill_md_path.resolve().as_uri()
    structure_map = build_structure_map(skill_dir)
    return serialize(skill_text, title, uri, structure_map, files, skill_dir)
