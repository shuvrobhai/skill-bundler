"""Bundle format contract: constants, serialization, and deserialization."""

import re
from pathlib import Path

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

# Default unpack directory
DEFAULT_UNPACK_DIR = "unpacked-skill"

# Title and header tokens
TITLE_PREFIX = "**Title:** One Page Version of "
COLLECTION_TITLE_PREFIX = "**Title:** Collection Bundle — "

# Source marker comments
SOURCE_COMMENT_PREFIX = "<!-- SOURCE:"
SOURCE_COMMENT_SUFFIX = "-->"
SOURCE_PATTERN = re.compile(r"(?m)^<!-- SOURCE:\s*(.*?)\s*-->\r?$")

# Skill marker and binary handling
SKILL_MARKER_RELATIVE_PATH = "SKILL.md"
BINARY_NOTICE = "_binary file — not inlined_"
BINARY_PROBE_SIZE = 8192


def _build_code_fence(content: str, lang: str) -> tuple[str, str]:
    """Return (opening_fence, closing_fence) avoiding collision with backticks in content."""
    max_run = max((len(match) for match in re.findall(r"`+", content)), default=0)
    backtick_fence = "`" * max(3, max_run + 1)
    opening = f"{backtick_fence}{lang}" if lang else backtick_fence
    return opening, backtick_fence


def serialize(
    skill_text: str,
    title: str,
    uri: str,
    structure_map: str,
    files: list[Path],
    skill_dir: Path,
) -> tuple[str, int, list[str]]:
    """Assemble a Markdown bundle document from pre-computed skill metadata and files."""
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
            lines.extend(
                [
                    f"{SOURCE_COMMENT_PREFIX} {relative_path} {SOURCE_COMMENT_SUFFIX}",
                    "",
                    f"## {relative_path}",
                    "",
                    BINARY_NOTICE,
                    "",
                ]
            )
            continue

        lang = EXTENSION_LANGUAGE_TAGS.get(path.suffix.lower(), "")
        opening, closing = _build_code_fence(content, lang)

        lines.extend(
            [
                f"{SOURCE_COMMENT_PREFIX} {relative_path} {SOURCE_COMMENT_SUFFIX}",
                "",
                f"## {relative_path}",
                "",
                opening,
                content.rstrip("\n"),
                closing,
                "",
            ]
        )
        inlined_count += 1

    document = "\n".join(lines)
    return document, inlined_count, skipped_files


def deserialize(bundle_text: str) -> tuple[dict[str, str], list[str]]:
    """
    Parse a bundle document into extracted text files and skipped binary files.

    Returns:
        (files_dict, skipped_files_list)
        where files_dict maps relative_path -> string_content.
    """
    if (
        bundle_text.startswith(COLLECTION_TITLE_PREFIX)
        or "**Title:** Collection Bundle" in bundle_text
    ):
        raise ValueError("Collection Bundles cannot be unpacked.")

    if f"<!-- SOURCE: {SKILL_MARKER_RELATIVE_PATH} -->" not in bundle_text:
        raise ValueError(
            f"Invalid bundle: missing '<!-- SOURCE: {SKILL_MARKER_RELATIVE_PATH} -->' marker."
        )

    candidate_matches = list(SOURCE_PATTERN.finditer(bundle_text))

    valid_sections: list[tuple[str, int, int]] = []
    seen_paths: set[str] = set()

    for match in candidate_matches:
        rel_path = match.group(1).strip()
        if rel_path in seen_paths:
            continue

        # Verify that match is followed by '## <rel_path>' header
        after_match = bundle_text[match.end() :]
        header_check = re.match(
            rf"^\s*\r?\n##\s+{re.escape(rel_path)}(\r?\n|$)", after_match
        )
        if not header_check:
            continue

        valid_sections.append((rel_path, match.start(), match.end()))
        seen_paths.add(rel_path)

    if not valid_sections:
        raise ValueError("Invalid bundle: no file sections found.")

    files: dict[str, str] = {}
    skipped_files: list[str] = []

    for idx, (relative_path, start_pos, end_pos) in enumerate(valid_sections):
        next_start = (
            valid_sections[idx + 1][1]
            if idx + 1 < len(valid_sections)
            else len(bundle_text)
        )
        section_text = bundle_text[end_pos:next_start].strip()

        header_pattern = rf"^##\s+{re.escape(relative_path)}\s*\r?\n*"
        content_body = re.sub(header_pattern, "", section_text, count=1).strip()

        if content_body == BINARY_NOTICE:
            skipped_files.append(relative_path)
            continue

        if relative_path == SKILL_MARKER_RELATIVE_PATH:
            files[relative_path] = content_body
            continue

        fence_match = re.match(
            r"^(`{3,})[^\n]*\r?\n?(.*?)\r?\n?\1\s*$", content_body, re.DOTALL
        )
        files[relative_path] = fence_match.group(2) if fence_match else content_body

    if SKILL_MARKER_RELATIVE_PATH not in files:
        raise ValueError(
            f"Invalid bundle: {SKILL_MARKER_RELATIVE_PATH} content was not extracted."
        )

    return files, skipped_files
