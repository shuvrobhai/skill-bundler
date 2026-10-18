"""Frontmatter parsing utilities for SKILL.md documents."""

from pathlib import Path
from typing import Tuple, Union


def parse_skill_text(text: str) -> Tuple[str, str, str]:
    """
    Parse SKILL.md content into (name, description, body).
    
    Splits strictly on the first two '---' markers to preserve any horizontal
    rules or markdown dividers in the body. Supports folded (>) and literal (|)
    multiline YAML descriptions.
    """
    name = ""
    description = ""
    body = text

    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return name, description, body

    # Find the closing '---' line
    closing_index = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            closing_index = i
            break

    if closing_index == -1:
        # No closing delimiter found; treated as plain body
        return name, description, body

    frontmatter_lines = lines[1:closing_index]
    body = "".join(lines[closing_index + 1:]).lstrip("\n")

    # Parse frontmatter lines with multiline support
    idx = 0
    while idx < len(frontmatter_lines):
        line = frontmatter_lines[idx].rstrip("\r\n")

        # Top-level keys must not be indented
        is_top_level = bool(line) and not line.startswith((" ", "\t"))
        stripped = line.strip()

        if is_top_level and stripped.startswith("name:"):
            name = stripped.split(":", 1)[1].strip().strip("\"'")
            idx += 1
        elif is_top_level and stripped.startswith("description:"):
            raw_val = stripped.split(":", 1)[1].strip()
            if raw_val in (">", ">-", ">+", "|", "|-", "|+"):
                is_folded = raw_val.startswith(">")
                desc_parts = []
                idx += 1
                while idx < len(frontmatter_lines):
                    next_line = frontmatter_lines[idx].rstrip("\r\n")
                    if next_line and not next_line.startswith((" ", "\t")):
                        # Next top-level key encountered
                        break
                    desc_parts.append(next_line.strip())
                    idx += 1
                joiner = " " if is_folded else "\n"
                description = joiner.join(part for part in desc_parts if part).strip()
            else:
                description = raw_val.strip("\"'")
                idx += 1
        else:
            idx += 1

    return name, description, body


def parse_skill(skill_source: Union[Path, str]) -> Tuple[str, str, str]:
    """
    Return (name, description, body) from a SKILL.md file Path or string content.
    """
    if isinstance(skill_source, Path):
        text = skill_source.read_text(encoding="utf-8")
    else:
        text = str(skill_source)
    return parse_skill_text(text)
