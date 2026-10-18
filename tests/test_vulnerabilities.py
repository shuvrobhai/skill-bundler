"""Reproduction and regression test cases for security and boundary protections."""

import tempfile
import unittest
from pathlib import Path

from bundium.unpacker import (
    UnpackError,
    check_collisions,
    extract_skill_title,
    is_safe_relative_path,
    parse_bundle,
    unpack_bundle,
    validate_paths,
    write_files,
)


class TestVulnerabilitiesReproduction(unittest.TestCase):
    """Verifies protections against path traversal, substring collisions, and delimiter splitting."""

    def test_title_sanitization_traversal(self):
        """Bundle title of '..', '.', or hidden name must fallback to unpacked-skill."""
        for unsafe_title in ["..", ".", ".hidden", "../escape"]:
            bundle = f"**Title:** One Page Version of {unsafe_title}\n"
            sanitized = extract_skill_title(bundle)
            self.assertEqual(
                sanitized,
                "unpacked-skill",
                f"Unsafe title '{unsafe_title}' must fall back to 'unpacked-skill'",
            )

    def test_binary_marker_substring_collision(self):
        """A text file containing '_binary file — not inlined_' must not be dropped."""
        bundle_with_binary_substring = (
            "**Title:** One Page Version of dogfood\n\n"
            "<!-- SOURCE: SKILL.md -->\n\n## SKILL.md\n\nSample Skill\n\n"
            "<!-- SOURCE: checker.py -->\n\n## checker.py\n\n```python\n"
            'MARKER = "_binary file — not inlined_"\n'
            "```\n"
        )
        files, skipped = parse_bundle(bundle_with_binary_substring)
        self.assertNotIn("checker.py", skipped)
        self.assertIn("checker.py", files)
        self.assertIn('MARKER = "_binary file — not inlined_"', files["checker.py"])

    def test_delimiter_collision_in_code_block(self):
        """A file with an inlined <!-- SOURCE: ... --> inside a code block must not cause phantom files."""
        bundle_with_delimiter = (
            "**Title:** One Page Version of documentation\n\n"
            "## Skill's Structure Map\n```\n"
            "docs/guide.md\n"
            "```\n\n"
            "<!-- SOURCE: SKILL.md -->\n\n## SKILL.md\n\nDocumentation\n\n"
            "<!-- SOURCE: docs/guide.md -->\n\n## docs/guide.md\n\n```markdown\n"
            "Example comment:\n<!-- SOURCE: phantom.py -->\nCode here\n```\n"
        )
        files, _ = parse_bundle(bundle_with_delimiter)
        self.assertNotIn("phantom.py", files)
        self.assertIn("docs/guide.md", files)
        self.assertIn("<!-- SOURCE: phantom.py -->", files["docs/guide.md"])

    def test_delimiter_collision_with_declared_file_in_skill_md(self):
        """SKILL.md containing a comment shaped like a declared file marker must not truncate SKILL.md."""
        bundle = (
            "**Title:** One Page Version of self-ref\n\n"
            "# Skill's Structure Map\n```text\nself-ref\nSKILL.md\nhelper.py\n```\n\n"
            "<!-- SOURCE: SKILL.md -->\n\n## SKILL.md\n\n"
            "First part of SKILL.md\n"
            "<!-- SOURCE: helper.py -->\n"
            "Second part of SKILL.md that must not be lost\n\n"
            "<!-- SOURCE: helper.py -->\n\n## helper.py\n\n```python\n"
            "print('actual helper')\n"
            "```\n"
        )
        files, _ = parse_bundle(bundle)
        self.assertIn("Second part of SKILL.md that must not be lost", files["SKILL.md"])
        self.assertEqual(files["helper.py"], "print('actual helper')")

    def test_self_referential_delimiter_inside_code_file(self):
        """A source file containing <!-- SOURCE: <itself> --> must not be split in half."""
        bundle = (
            "**Title:** One Page Version of self-code\n\n"
            "# Skill's Structure Map\n```text\nself-code\nSKILL.md\ncode.py\n```\n\n"
            "<!-- SOURCE: SKILL.md -->\n\n## SKILL.md\n\nMain Skill\n\n"
            "<!-- SOURCE: code.py -->\n\n## code.py\n\n```python\n"
            "# Top of code\n"
            "DELIM = '<!-- SOURCE: code.py -->'\n"
            "# Bottom of code\n"
            "```\n"
        )
        files, _ = parse_bundle(bundle)
        self.assertIn("# Top of code", files["code.py"])
        self.assertIn("# Bottom of code", files["code.py"])

    def test_dest_equals_target_resolved_rejected(self):
        """A relative path that resolves to the destination directory itself must be rejected."""
        dest = Path("/tmp/target_destination").resolve()
        self.assertFalse(is_safe_relative_path(dest, dest))
        self.assertFalse(is_safe_relative_path(dest / ".", dest))
        self.assertFalse(is_safe_relative_path(dest / "..", dest))

    def test_collection_bundle_rejection(self):
        """Collection Bundles must be rejected explicitly."""
        collection_bundle = (
            "**Title:** Collection Bundle — my-collection\n\n"
            "**Skills:** 2\n\n"
            "<!-- SOURCE: skill-a/SKILL.md -->\n\nSkill A\n"
        )
        with self.assertRaises(UnpackError) as ctx:
            parse_bundle(collection_bundle)
        self.assertEqual(str(ctx.exception), "Collection Bundles cannot be unpacked.")

    def test_validate_paths_rejects_traversal_independently(self):
        target_dir = Path(tempfile.mkdtemp())
        with self.assertRaises(UnpackError) as ctx:
            validate_paths({"../escape.py": "content"}, target_dir)
        self.assertIn("Security violation", str(ctx.exception))

    def test_check_collisions_rejects_existing_files(self):
        target_dir = Path(tempfile.mkdtemp())
        (target_dir / "clash.txt").write_text("existing", encoding="utf-8")
        with self.assertRaises(UnpackError) as ctx:
            check_collisions({"clash.txt": "new"}, target_dir, should_overwrite=False)
        self.assertIn("Use --force", str(ctx.exception))

    def test_write_files_creates_nested_structure(self):
        target_dir = Path(tempfile.mkdtemp()) / "out"
        write_files({"a/b/c.txt": "deep"}, target_dir)
        self.assertTrue((target_dir / "a" / "b" / "c.txt").is_file())


if __name__ == "__main__":
    unittest.main()
