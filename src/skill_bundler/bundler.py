"""Core domain logic for bundling a skill directory into a Markdown document."""

import re
import sys
from pathlib import Path
from typing import List, Tuple

EXTENSION_LANGUAGE_TAGS = {
    ".py": "python",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".sh": "bash",
    ".txt": "text",
    ".html": "html",
    ".css": "css",
    ".js": "javascript",
    ".ts": "typescript",
    ".sql": "sql",
}

BINARY_PROBE_SIZE = 8192


def parse_skill(skill_md_path: Path) -> Tuple[str, str, str]:
    """Return (name, description, body) from SKILL.md."""
    text = skill_md_path.read_text(encoding="utf-8")
    name = ""
    description = ""
    body = text

    # Simple key:value frontmatter parser
    if text.startswith("---"):
        parts = re.split(r"^---\s*$", text, maxsplit=2, flags=re.MULTILINE)
        if len(parts) >= 3:
            frontmatter = parts[1]
            body = parts[2].lstrip("\n")
            for line in frontmatter.splitlines():
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip().strip("\"'")
                elif line.startswith("description:"):
                    description = line.split(":", 1)[1].strip().strip("\"'")

    return name, description, body


def collect_skill_files(skill_dir: Path) -> List[Path]:
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
        if any(part.startswith(".") for part in relative_path.parts):
            continue
        if "__pycache__" in relative_path.parts:
            continue

        files.append(path)

    return files


def _tree_sort_key(path: Path):
    """SKILL.md first, then directories, then other files."""
    if path.name == "SKILL.md":
        return (0, 0, "")
    if path.is_dir():
        return (0, 1, path.name.lower())
    return (1, 0, path.name.lower())


def _tree_body(directory: Path, prefix: str, lines: List[str]) -> None:
    entries = sorted(
        [
            p
            for p in directory.iterdir()
            if not p.name.startswith(".")
            and p.name != "__pycache__"
            and not p.is_symlink()
        ],
        key=_tree_sort_key,
    )

    for i, path in enumerate(entries):
        is_last = i == len(entries) - 1
        connector = "└── " if is_last else "├── "
        lines.append(prefix + connector + path.name)

        if path.is_dir():
            child_prefix = "    " if is_last else "│   "
            _tree_body(path, prefix + child_prefix, lines)


def directory_tree(skill_dir: Path) -> str:
    """Return a text tree representation (Structure Map) of the skill directory."""
    lines = [skill_dir.name]
    _tree_body(skill_dir, "", lines)
    return "\n".join(lines)


def _code_fence(content: str, lang: str) -> Tuple[str, str]:
    """Return (opening_fence, closing_fence) avoiding collision with backticks in content."""
    max_run = 0
    current_run = 0
    for ch in content:
        if ch == "`":
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 0

    backtick_fence = "`" * max(3, max_run + 1)
    opening = f"{backtick_fence}{lang}" if lang else backtick_fence
    return opening, backtick_fence


def build_bundle_document(
    skill_dir: Path, skill_md_path: Path, files: List[Path]
) -> Tuple[str, int, List[str]]:
    """Build one Markdown document with metadata, structure map, and inlined files."""
    name, description, body = parse_skill(skill_md_path)
    title = name or skill_dir.name
    uri = skill_md_path.resolve().as_uri()
    tree = directory_tree(skill_dir)

    skill_text = skill_md_path.read_text(encoding="utf-8")

    lines = [
        f"**Title:** One Page Version of {title}",
        "",
        f"**Source:** [{uri}]({uri})",
        "",
        "---",
        "",
        "# Skill's Structure Map",
        "",
        "```text",
        tree,
        "```",
        "",
        "---",
        "",
        "<!-- SOURCE: SKILL.md -->",
        "",
        "## SKILL.md",
        "",
        skill_text.rstrip("\n"),
        "",
    ]

    inlined_count = 0
    skipped_files: List[str] = []

    for path in files:
        relative_path = path.relative_to(skill_dir).as_posix()
        file_bytes = path.read_bytes()

        if b"\x00" in file_bytes[:BINARY_PROBE_SIZE]:
            skipped_files.append(relative_path)
            lines.extend([
                f"<!-- SOURCE: {relative_path} -->",
                "",
                f"## {relative_path}",
                "",
                "_binary file — not inlined_",
                "",
            ])
            continue

        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            skipped_files.append(relative_path)
            lines.extend([
                f"<!-- SOURCE: {relative_path} -->",
                "",
                f"## {relative_path}",
                "",
                "_binary file — not inlined_",
                "",
            ])
            continue

        lang = EXTENSION_LANGUAGE_TAGS.get(path.suffix.lower(), "")
        opening, closing = _code_fence(content, lang)

        lines.extend([
            f"<!-- SOURCE: {relative_path} -->",
            "",
            f"## {relative_path}",
            "",
            opening,
            content.rstrip("\n"),
            closing,
            "",
        ])
        inlined_count += 1

    return "\n".join(lines), inlined_count, skipped_files


def validate_output(
    output_text: str, skill_body: str, non_skill_file_count: int
) -> None:
    """Basic runnable check that the output contains the expected pieces."""
    if "Skill's Structure Map" not in output_text:
        sys.exit("Validation failed: structure map is missing.")

    if skill_body and skill_body.strip()[:200] not in output_text:
        sys.exit("Validation failed: SKILL.md body is missing from output.")

    if non_skill_file_count > 0:
        expected_comments = non_skill_file_count + 1  # SKILL.md + inlined + skipped files
        if output_text.count("<!-- SOURCE:") < expected_comments:
            sys.exit("Validation failed: not all source separators made it into output.")
