"""skill_bundler package."""

from skill_bundler.bundler import (
    build_bundle_document,
    build_structure_map,
    collect_skill_files,
    parse_skill,
)
from skill_bundler.clipboard import (
    ClipboardError,
    copy_to_clipboard,
    paste_from_clipboard,
)
from skill_bundler.indexer import (
    SkillEntry,
    build_collection_document,
    discover_skills,
)
from skill_bundler.unpacker import (
    UnpackError,
    extract_skill_title,
    parse_bundle,
    unpack_bundle,
)

# Backwards compatibility alias
directory_tree = build_structure_map

__version__ = "0.2.1"
__all__ = [
    "__version__",
    "ClipboardError",
    "SkillEntry",
    "UnpackError",
    "build_bundle_document",
    "build_collection_document",
    "build_structure_map",
    "collect_skill_files",
    "copy_to_clipboard",
    "directory_tree",
    "discover_skills",
    "extract_skill_title",
    "parse_bundle",
    "parse_skill",
    "paste_from_clipboard",
    "unpack_bundle",
]
