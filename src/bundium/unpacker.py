"""Unpack a skill bundle back into a directory structure on disk."""

import re
from pathlib import Path

from bundium.bundle_format import DEFAULT_UNPACK_DIR, deserialize


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


def parse_bundle(bundle_text: str) -> tuple[dict[str, str], list[str]]:
    """Parse a bundle document into extracted text files and skipped binary files."""
    try:
        return deserialize(bundle_text)
    except ValueError as err:
        raise UnpackError(str(err))


def validate_paths(files: dict[str, str], target_dir: Path) -> None:
    """Validate that all relative paths are safe. Raises UnpackError on violation."""
    for relative_path in files.keys():
        if not is_safe_relative_path(target_dir, relative_path):
            raise UnpackError(
                f"Security violation: unsafe path '{relative_path}' attempts to escape target directory."
            )


def check_collisions(files: dict[str, str], target_dir: Path, should_overwrite: bool = False) -> None:
    """Check for existing files. Raises UnpackError if conflicts found and not overwriting."""
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


def write_files(files: dict[str, str], target_dir: Path) -> int:
    """Write all files to target_dir. Returns count of written files."""
    target_dir.mkdir(parents=True, exist_ok=True)
    unpacked_count = 0
    for relative_path, content in files.items():
        dest_path = target_dir / relative_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        if content and not content.endswith("\n"):
            content = content + "\n"
        dest_path.write_text(content, encoding="utf-8")
        unpacked_count += 1
    return unpacked_count


def is_safe_relative_path(target_dir: Path, relative_path_str: str) -> bool:
    """Ensure relative path does not escape target directory (prevent directory traversal)."""
    try:
        relative_path = Path(relative_path_str)
        if relative_path.is_absolute():
            return False
        dest = (target_dir / relative_path).resolve()
        target_resolved = target_dir.resolve()
        return dest.is_relative_to(target_resolved) and dest != target_resolved
    except Exception:
        return False


def unpack_bundle(
    bundle_text: str,
    target_dir: Path,
    should_overwrite: bool = False,
) -> tuple[int, list[str]]:
    """
    Unpack bundle files into target_dir on disk.
    
    Args:
        bundle_text: The complete Markdown bundle content.
        target_dir: Destination directory.
        should_overwrite: If True, overwrite existing files without error.
        
    Returns:
        (unpacked_count, skipped_files)
    """
    files, skipped_files = parse_bundle(bundle_text)
    target_dir = target_dir.resolve()

    validate_paths(files, target_dir)
    check_collisions(files, target_dir, should_overwrite)
    unpacked_count = write_files(files, target_dir)

    return unpacked_count, skipped_files
