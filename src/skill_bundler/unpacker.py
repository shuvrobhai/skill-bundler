"""Unpack a skill bundle back into a directory structure on disk."""

import re
from pathlib import Path

from skill_bundler.constants import (
    BINARY_NOTICE,
    COLLECTION_TITLE_PREFIX,
    DEFAULT_UNPACK_DIR,
    SKILL_MARKER_RELATIVE_PATH,
    SOURCE_PATTERN,
)


class UnpackError(Exception):
    """Raised when bundle parsing or unpacking fails."""
    pass


def extract_skill_title(bundle_text: str) -> str:
    """Extract skill title from '**Title:** One Page Version of {title}' or default."""
    match = re.search(r"\*\*Title:\*\*\s*One Page Version of\s*(.+)", bundle_text)
    if match:
        title = match.group(1).strip()
        # Clean title for filesystem directory naming
        sanitized = re.sub(r"[^\w\-.]", "-", title).strip("-")
        # Reject empty, dot-only ('.', '..'), or hidden directory names
        if not sanitized or set(sanitized) == {"."} or sanitized.startswith("."):
            return DEFAULT_UNPACK_DIR
        return sanitized
    return DEFAULT_UNPACK_DIR


def parse_structure_map_paths(bundle_text: str) -> set[str]:
    """Extract relative file paths declared in the Structure Map preamble."""
    match = re.search(
        r"#{1,3}\s*Skill's Structure Map\s+```[a-zA-Z]*\s*\r?\n(.*?)\r?\n```",
        bundle_text,
        re.DOTALL,
    )
    if not match:
        return set()

    tree_lines = match.group(1).splitlines()
    if not tree_lines:
        return set()

    paths = set()
    stack: list[str] = []

    for line in tree_lines:
        connector_match = re.search(r"[└├]── ", line)
        if connector_match:
            depth = connector_match.start() // 4
            entry_name = line[connector_match.end():].strip()
            if entry_name:
                stack = stack[:depth]
                stack.append(entry_name)
                paths.add("/".join(stack))
        else:
            cleaned = line.strip()
            if cleaned and not cleaned.startswith("#") and "/" in cleaned:
                paths.add(cleaned)

    return paths


def parse_bundle(bundle_text: str) -> tuple[dict[str, str], list[str]]:
    """
    Parse a bundle document into extracted text files and skipped binary files.
    
    Returns:
        (files_dict, skipped_files_list)
        where files_dict maps relative_path -> string_content.
    """
    if bundle_text.startswith(COLLECTION_TITLE_PREFIX) or "**Title:** Collection Bundle" in bundle_text:
        raise UnpackError("Collection Bundles cannot be unpacked.")

    if f"<!-- SOURCE: {SKILL_MARKER_RELATIVE_PATH} -->" not in bundle_text:
        raise UnpackError(
            f"Invalid bundle: missing '<!-- SOURCE: {SKILL_MARKER_RELATIVE_PATH} -->' marker."
        )

    declared_paths = parse_structure_map_paths(bundle_text)

    # Locate all line-anchored SOURCE markers
    candidate_matches = list(SOURCE_PATTERN.finditer(bundle_text))

    # Filter matches to valid declared paths or SKILL.md to avoid splitting on inlined examples
    valid_sections: list[tuple[str, int, int]] = []
    for match in candidate_matches:
        rel_path = match.group(1).strip()
        # Accept if it's SKILL.md, or in declared Structure Map, or if no Structure Map was present
        if rel_path == SKILL_MARKER_RELATIVE_PATH or not declared_paths or rel_path in declared_paths:
            valid_sections.append((rel_path, match.start(), match.end()))

    if not valid_sections:
        raise UnpackError("Invalid bundle: no file sections found.")

    files: dict[str, str] = {}
    skipped_files: list[str] = []

    for idx, (relative_path, start_pos, end_pos) in enumerate(valid_sections):
        next_start = valid_sections[idx + 1][1] if idx + 1 < len(valid_sections) else len(bundle_text)
        section_text = bundle_text[end_pos:next_start].strip()

        # Remove header '## <path>' if present at start
        header_pattern = rf"^##\s+{re.escape(relative_path)}\s*\r?\n*"
        content_body = re.sub(header_pattern, "", section_text, count=1).strip()

        # Exact match check for binary file notice
        if content_body == BINARY_NOTICE:
            skipped_files.append(relative_path)
            continue

        if relative_path == SKILL_MARKER_RELATIVE_PATH:
            files[relative_path] = content_body
            continue

        # Extract content inside code fences (3 or more backticks)
        fence_match = re.match(
            r"^(`{3,})[^\n]*\r?\n?(.*?)\r?\n?\1\s*$", content_body, re.DOTALL
        )
        files[relative_path] = fence_match.group(2) if fence_match else content_body

    if SKILL_MARKER_RELATIVE_PATH not in files:
        raise UnpackError(f"Invalid bundle: {SKILL_MARKER_RELATIVE_PATH} content was not extracted.")

    return files, skipped_files


def is_safe_relative_path(target_dir: Path, relative_path_str: str) -> bool:
    """Ensure relative path does not escape target directory (prevent directory traversal)."""
    try:
        relative_path = Path(relative_path_str)
        if relative_path.is_absolute():
            return False
        dest = (target_dir / relative_path).resolve()
        target_resolved = target_dir.resolve()
        # Disallow resolving to target_dir itself (file entry cannot be root)
        if dest == target_resolved:
            return False
        return target_resolved in dest.parents
    except Exception:
        return False


def unpack_bundle(
    bundle_text: str,
    target_dir: Path,
    should_overwrite: bool = False,
    force: bool = False,
) -> tuple[int, list[str]]:
    """
    Unpack bundle files into target_dir on disk.
    
    Args:
        bundle_text: The complete Markdown bundle content.
        target_dir: Destination directory.
        should_overwrite: If True, overwrite existing files without error.
        force: Backwards-compatible alias for should_overwrite.
        
    Returns:
        (unpacked_count, skipped_files)
    """
    if force:
        should_overwrite = True

    files, skipped_files = parse_bundle(bundle_text)
    target_dir = target_dir.resolve()

    # 1. Path safety check
    for relative_path in files.keys():
        if not is_safe_relative_path(target_dir, relative_path):
            raise UnpackError(
                f"Security violation: unsafe path '{relative_path}' attempts to escape target directory."
            )

    # 2. Collision check
    existing_conflicts = [
        relative_path
        for relative_path in files.keys()
        if (target_dir / relative_path).exists()
    ]

    if existing_conflicts and not should_overwrite:
        conflict_list = "\n".join(f"  - {p}" for p in existing_conflicts)
        raise UnpackError(
            f"Destination directory contains {len(existing_conflicts)} existing file(s):\n"
            f"{conflict_list}\n"
            f"Use --force (-f) to overwrite existing files."
        )

    # 3. Write files
    target_dir.mkdir(parents=True, exist_ok=True)
    unpacked_count = 0

    for relative_path, content in files.items():
        dest_path = target_dir / relative_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        if content and not content.endswith("\n"):
            content = content + "\n"
        dest_path.write_text(content, encoding="utf-8")
        unpacked_count += 1

    return unpacked_count, skipped_files
