"""bundium package."""

from bundium.bundler import (
    build_bundle_document,
    build_structure_map,
    collect_skill_files,
)
from bundium.frontmatter import parse_skill
from bundium.clipboard import (
    ClipboardError,
    copy_to_clipboard,
    paste_from_clipboard,
)
from bundium.indexer import (
    SkillEntry,
    build_collection_document,
    discover_skills,
)
from bundium.unpacker import (
    UnpackError,
    extract_skill_title,
    parse_bundle,
    unpack_bundle,
)

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
    "discover_skills",
    "extract_skill_title",
    "parse_bundle",
    "parse_skill",
    "paste_from_clipboard",
    "unpack_bundle",
]
