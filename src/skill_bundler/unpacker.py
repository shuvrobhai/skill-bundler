"""Unpack a skill bundle back into a directory structure on disk."""

import re
from pathlib import Path


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
        return sanitized or "unpacked-skill"
    return "unpacked-skill"


def parse_bundle(bundle_text: str) -> tuple[dict[str, str], list[str]]:
    """
    Parse a bundle document into extracted text files and skipped binary files.
    
    Returns:
        (files_dict, skipped_files_list)
        where files_dict maps relative_path -> string_content.
    """
    if "<!-- SOURCE: SKILL.md -->" not in bundle_text:
        raise UnpackError(
            "Invalid bundle: missing '<!-- SOURCE: SKILL.md -->' marker."
        )

    # Split by SOURCE comments: <!-- SOURCE: <relative_path> -->
    pattern = r"<!-- SOURCE:\s*(.*?)\s*-->"
    parts = re.split(pattern, bundle_text)
    
    # parts[0] is preamble / title / structure map
    # parts[1] is path1, parts[2] is section1, parts[3] is path2, parts[4] is section2...
    if len(parts) < 3:
        raise UnpackError("Invalid bundle: no file sections found.")

    files: dict[str, str] = {}
    skipped_files: list[str] = []

    for i in range(1, len(parts), 2):
        relative_path = parts[i].strip()
        section_text = parts[i + 1].strip()

        # Remove header '## <path>' if present at start
        header_pattern = rf"^##\s+{re.escape(relative_path)}\s*\n*"
        content_body = re.sub(header_pattern, "", section_text, count=1).strip()

        if "_binary file — not inlined_" in content_body:
            skipped_files.append(relative_path)
            continue

        if relative_path == "SKILL.md":
            files[relative_path] = content_body
            continue

        # Extract content inside code fences (3 or more backticks)
        fence_match = re.match(
            r"^(`{3,})[^\n]*\n?(.*?)\n?\1\s*$", content_body, re.DOTALL
        )
        files[relative_path] = fence_match.group(2) if fence_match else content_body

    if "SKILL.md" not in files:
        raise UnpackError("Invalid bundle: SKILL.md content was not extracted.")

    return files, skipped_files


def is_safe_relative_path(target_dir: Path, relative_path_str: str) -> bool:
    """Ensure relative path does not escape target directory (prevent directory traversal)."""
    try:
        relative_path = Path(relative_path_str)
        if relative_path.is_absolute():
            return False
        dest = (target_dir / relative_path).resolve()
        target_resolved = target_dir.resolve()
        return dest == target_resolved or target_resolved in dest.parents
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
