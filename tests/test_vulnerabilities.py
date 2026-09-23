"""Reproduction and regression test cases for security and boundary protections."""

import tempfile
import unittest
from pathlib import Path

from skill_bundler.unpacker import (
    UnpackError,
    extract_skill_title,
    is_safe_relative_path,
    parse_bundle,
    unpack_bundle,
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


if __name__ == "__main__":
    unittest.main()
