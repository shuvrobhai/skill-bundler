"""Centralized constants, markers, and patterns for skill-bundler."""

import re

# Marker comments and patterns
SOURCE_COMMENT_PREFIX = "<!-- SOURCE:"
SOURCE_COMMENT_SUFFIX = "-->"
SOURCE_PATTERN = re.compile(r"(?m)^<!-- SOURCE:\s*(.*?)\s*-->\r?$")

SKILL_MARKER_RELATIVE_PATH = "SKILL.md"
SKILL_MARKER_COMMENT = f"{SOURCE_COMMENT_PREFIX} {SKILL_MARKER_RELATIVE_PATH} {SOURCE_COMMENT_SUFFIX}"

# Binary file handling
BINARY_NOTICE = "_binary file — not inlined_"
BINARY_PROBE_SIZE = 8192

# Titles and default paths
TITLE_PREFIX = "**Title:** One Page Version of "
COLLECTION_TITLE_PREFIX = "**Title:** Collection Bundle — "
DEFAULT_UNPACK_DIR = "unpacked-skill"

# Code fence language tags
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
