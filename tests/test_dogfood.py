"""Dogfooding and independent marker contract test cases."""

import tempfile
import unittest
from pathlib import Path

from skill_bundler.bundler import build_bundle_document, collect_skill_files
from skill_bundler.constants import (
    BINARY_NOTICE,
    COLLECTION_TITLE_PREFIX,
    SKILL_MARKER_RELATIVE_PATH,
    SOURCE_COMMENT_PREFIX,
    SOURCE_COMMENT_SUFFIX,
    SOURCE_PATTERN,
    TITLE_PREFIX,
)
from skill_bundler.unpacker import parse_bundle, unpack_bundle


class TestMarkerContract(unittest.TestCase):
    """Verify that bundler and unpacker adhere to the centralized constants contract."""

    def test_constants_contract(self):
        self.assertEqual(SOURCE_COMMENT_PREFIX, "<!-- SOURCE:")
        self.assertEqual(SOURCE_COMMENT_SUFFIX, "-->")
        self.assertEqual(SKILL_MARKER_RELATIVE_PATH, "SKILL.md")
        self.assertEqual(BINARY_NOTICE, "_binary file — not inlined_")
        self.assertEqual(TITLE_PREFIX, "**Title:** One Page Version of ")
        self.assertEqual(COLLECTION_TITLE_PREFIX, "**Title:** Collection Bundle — ")

    def test_source_pattern_crlf_and_lf(self):
        lf_marker = "<!-- SOURCE: path/to/file.py -->\n"
        crlf_marker = "<!-- SOURCE: path/to/file.py -->\r\n"
        self.assertTrue(SOURCE_PATTERN.search(lf_marker))
        self.assertTrue(SOURCE_PATTERN.search(crlf_marker))


class TestDogfood(unittest.TestCase):
    """Dogfood packaging on a realistic codebase structure containing code and edge cases."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.skill_dir = Path(self.temp_dir.name) / "complex-skill"
        self.skill_dir.mkdir()

        # Write SKILL.md with frontmatter and body
        (self.skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: complex-skill\n"
            "description: >\n"
            "  A comprehensive skill for\n"
            "  dogfood testing.\n"
            "---\n\n"
            "# Complex Skill\n"
            "Here is the skill documentation.\n\n"
            "---\n"
            "Horizontal rule in SKILL.md\n",
            encoding="utf-8",
        )

        # Write subdirectories and files
        (self.skill_dir / "src").mkdir()
        (self.skill_dir / "src" / "code.py").write_text(
            '# Python file with tricky contents\n'
            'FAKE_DELIMITER = "<!-- SOURCE: fake.txt -->"\n'
            'FAKE_BINARY = "_binary file — not inlined_"\n'
            '```markdown\n'
            'def hello():\n'
            '    return "world"\n'
            '```\n',
            encoding="utf-8",
        )

        (self.skill_dir / "docs").mkdir()
        (self.skill_dir / "docs" / "readme.md").write_text(
            '# Readme\nHere is documentation with `inline code` and backticks:\n'
            '````text\n'
            '```python\n'
            'nested backticks\n'
            '```\n'
            '````\n',
            encoding="utf-8",
        )

        (self.skill_dir / "assets").mkdir()
        (self.skill_dir / "assets" / "data.bin").write_bytes(b"\x00\x01\x02\x03\x04")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dogfood_pack_and_unpack_roundtrip(self):
        skill_md = self.skill_dir / "SKILL.md"
        files = collect_skill_files(self.skill_dir)

        document, inlined_count, skipped_files = build_bundle_document(
            self.skill_dir, skill_md, files
        )

        self.assertEqual(inlined_count, 2)  # code.py and readme.md
        self.assertEqual(skipped_files, ["assets/data.bin"])

        unpack_dest = Path(self.temp_dir.name) / "unpacked"
        unpacked_count, skipped_unpacked = unpack_bundle(
            document, unpack_dest, should_overwrite=True
        )

        self.assertEqual(unpacked_count, 3)  # SKILL.md, code.py, readme.md
        self.assertEqual(skipped_unpacked, ["assets/data.bin"])

        # Compare files
        self.assertEqual(
            (self.skill_dir / "SKILL.md").read_text(encoding="utf-8"),
            (unpack_dest / "SKILL.md").read_text(encoding="utf-8"),
        )
        self.assertEqual(
            (self.skill_dir / "src" / "code.py").read_text(encoding="utf-8"),
            (unpack_dest / "src" / "code.py").read_text(encoding="utf-8"),
        )
        self.assertEqual(
            (self.skill_dir / "docs" / "readme.md").read_text(encoding="utf-8"),
            (unpack_dest / "docs" / "readme.md").read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
