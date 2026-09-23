"""Core domain logic for bundling a skill directory into a Markdown document."""

import re
from pathlib import Path

from skill_bundler.constants import (
    BINARY_NOTICE,
    BINARY_PROBE_SIZE,
    EXTENSION_LANGUAGE_TAGS,
    SKILL_MARKER_RELATIVE_PATH,
    SOURCE_COMMENT_PREFIX,
    SOURCE_COMMENT_SUFFIX,
    TITLE_PREFIX,
)
from skill_bundler.frontmatter import parse_skill, parse_skill_text


def is_excluded_path(path: Path) -> bool:
    """True when any part is hidden or a cache dir."""
    return any(part.startswith(".") for part in path.parts) or (
        "__pycache__" in path.parts
    )


def collect_skill_files(skill_dir: Path) -> list[Path]:
    """Return all non-hidden, non-symlink files except SKILL.md."""
    files = []
    for path in sorted(skill_dir.rglob("*")):
        if path.name == "SKILL.md":
            continue
        if path.is_symlink():
            continue
        if not path.is_file():
            continue

        relative_path = path.relative_to(skill_dir)
        if is_excluded_path(relative_path):
            continue

        files.append(path)

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


# Backwards compatibility alias
directory_tree = build_structure_map


def _build_code_fence(content: str, lang: str) -> tuple[str, str]:
    """Return (opening_fence, closing_fence) avoiding collision with backticks in content."""
    max_run = max((len(match) for match in re.findall(r"`+", content)), default=0)
    backtick_fence = "`" * max(3, max_run + 1)
    opening = f"{backtick_fence}{lang}" if lang else backtick_fence
    return opening, backtick_fence


def validate_output(
    output_text: str,
    skill_body: str,
    files: list[Path],
    skipped_files: list[str],
    skill_dir: Path,
) -> None:
    """Validate that the bundle document satisfies structural integrity constraints."""
    if "Skill's Structure Map" not in output_text:
        raise ValueError("Validation failed: structure map is missing.")

    if skill_body and skill_body.strip()[:200] not in output_text:
        raise ValueError("Validation failed: SKILL.md body is missing from output.")

    expected_skill_marker = f"{SOURCE_COMMENT_PREFIX} {SKILL_MARKER_RELATIVE_PATH} {SOURCE_COMMENT_SUFFIX}"
    if expected_skill_marker not in output_text:
        raise ValueError("Validation failed: SKILL.md source separator is missing.")

    for path in files:
        rel_posix = path.relative_to(skill_dir).as_posix()
        expected_marker = f"{SOURCE_COMMENT_PREFIX} {rel_posix} {SOURCE_COMMENT_SUFFIX}"
        if expected_marker not in output_text:
            raise ValueError(f"Validation failed: missing source separator for {rel_posix}")

    for skipped in skipped_files:
        expected_marker = f"{SOURCE_COMMENT_PREFIX} {skipped} {SOURCE_COMMENT_SUFFIX}"
        if expected_marker not in output_text:
            raise ValueError(f"Validation failed: missing source separator for skipped file {skipped}")


def build_bundle_document(
    skill_dir: Path, skill_md_path: Path, files: list[Path]
) -> tuple[str, int, list[str]]:
    """Build one Markdown document with metadata, structure map, and inlined files."""
    skill_text = skill_md_path.read_text(encoding="utf-8")
    name, description, body = parse_skill_text(skill_text)
    title = name or skill_dir.name
    uri = skill_md_path.resolve().as_uri()
    structure_map = build_structure_map(skill_dir)

    lines = [
        f"{TITLE_PREFIX}{title}",
        "",
        f"**Source:** [{uri}]({uri})",
        "",
        "---",
        "",
        "# Skill's Structure Map",
        "",
        "```text",
        structure_map,
        "```",
        "",
        "---",
        "",
        f"{SOURCE_COMMENT_PREFIX} {SKILL_MARKER_RELATIVE_PATH} {SOURCE_COMMENT_SUFFIX}",
        "",
        "## SKILL.md",
        "",
        skill_text.rstrip("\n"),
        "",
    ]

    inlined_count = 0
    skipped_files: list[str] = []

    for path in files:
        relative_path = path.relative_to(skill_dir).as_posix()
        file_bytes = path.read_bytes()

        is_binary = b"\x00" in file_bytes[:BINARY_PROBE_SIZE]
        content = None
        if not is_binary:
            try:
                content = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                pass

        if content is None:
            skipped_files.append(relative_path)
            lines.extend([
                f"{SOURCE_COMMENT_PREFIX} {relative_path} {SOURCE_COMMENT_SUFFIX}",
                "",
                f"## {relative_path}",
                "",
                BINARY_NOTICE,
                "",
            ])
            continue

        lang = EXTENSION_LANGUAGE_TAGS.get(path.suffix.lower(), "")
        opening, closing = _build_code_fence(content, lang)

        lines.extend([
            f"{SOURCE_COMMENT_PREFIX} {relative_path} {SOURCE_COMMENT_SUFFIX}",
            "",
            f"## {relative_path}",
            "",
            opening,
            content.rstrip("\n"),
            closing,
            "",
        ])
        inlined_count += 1

    document = "\n".join(lines)
    validate_output(document, body, files, skipped_files, skill_dir)
    return document, inlined_count, skipped_files
