"""Build one Markdown document that surveys a whole Collection."""

from pathlib import Path
from typing import NamedTuple

from skill_bundler.bundler import is_excluded_path
from skill_bundler.constants import (
    COLLECTION_TITLE_PREFIX,
    SOURCE_COMMENT_PREFIX,
    SOURCE_COMMENT_SUFFIX,
)
from skill_bundler.frontmatter import parse_skill

DESCRIPTION_LIMIT = 80


class SkillEntry(NamedTuple):
    name: str
    description: str
    relative_path: str
    skill_md: Path
    body: str = ""


def _truncate(text: str, limit: int) -> str:
    """Collapse whitespace to single spaces, cut to limit, append marker when cut."""
    collapsed = " ".join(text.split())
    if len(collapsed) > limit:
        return collapsed[:limit] + "…"
    return collapsed


def _table_cell(text: str) -> str:
    """Escape cell separators so a value stays inside one cell."""
    return text.replace("|", "\\|")


def _read_entry(collection_dir: Path, skill_md: Path) -> SkillEntry:
    """Read one SKILL.md into an entry, falling back to the dir name."""
    name, description, body = parse_skill(skill_md)
    return SkillEntry(
        name=name or skill_md.parent.name,
        description=description,
        relative_path=skill_md.relative_to(collection_dir).as_posix(),
        skill_md=skill_md,
        body=body,
    )


def discover_skills(
    collection_dir: Path, should_recursive: bool = False
) -> tuple[list[SkillEntry], list[str]]:
    """Return skills sorted by name plus skipped dir paths. Root SKILL.md never counts."""
    skills: list[SkillEntry] = []
    skipped: list[str] = []

    def _explore(directory: Path) -> None:
        try:
            children = sorted(directory.iterdir())
        except OSError:
            return

        for child in children:
            if not child.is_dir() or child.is_symlink():
                continue
            relative = child.relative_to(collection_dir)
            if is_excluded_path(relative):
                continue
            skill_md = child / "SKILL.md"
            if skill_md.is_file():
                skills.append(_read_entry(collection_dir, skill_md))
                # Prune: do not traverse into internal subdirectories of a discovered skill
            else:
                skipped.append(relative.as_posix())
                if should_recursive:
                    _explore(child)

    _explore(collection_dir)
    skills.sort(key=lambda entry: entry.name.lower())
    skipped.sort()
    return skills, skipped


def build_collection_document(
    collection_dir: Path, skills: list[SkillEntry]
) -> str:
    """Return the Collection Bundle text for skills in the given order."""
    if not skills:
        raise ValueError("No skills found in collection.")

    uri = collection_dir.resolve().as_uri()
    lines = [
        f"{COLLECTION_TITLE_PREFIX}{collection_dir.name}",
        "",
        f"**Source:** [{uri}]({uri})",
        "",
        f"**Skills:** {len(skills)}",
        "",
        "---",
        "",
        "# Skill Index",
        "",
        "| Skill | Description | Path |",
        "|---|---|---|",
    ]
    for entry in skills:
        cell = _table_cell(_truncate(entry.description, DESCRIPTION_LIMIT))
        lines.append(f"| {entry.name} | {cell} | {entry.relative_path} |")
    lines.extend(["", "---", ""])

    for position, entry in enumerate(skills):
        body = entry.body if entry.body else parse_skill(entry.skill_md)[2]
        lines.extend(
            [
                f"{SOURCE_COMMENT_PREFIX} {entry.relative_path} {SOURCE_COMMENT_SUFFIX}",
                "",
                f"## {entry.name}",
                "",
                body.rstrip("\n"),
                "",
            ]
        )
        if position < len(skills) - 1:
            lines.extend(["---", ""])

    return "\n".join(lines)
