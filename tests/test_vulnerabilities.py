"""Reproduction test cases for discovered blind spots and boundary vulnerabilities."""

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
    """Demonstrates and tests vulnerabilities discovered by the analysts."""

    def test_title_sanitization_traversal(self):
        """Bundle title of '..' must not resolve to '..' and escape destination."""
        dot_bundle = "**Title:** One Page Version of ..\n"
        dot_title = extract_skill_title(dot_bundle)
        # Demonstrates the vulnerability: currently returns '..'
        self.assertEqual(
            dot_title,
            "..",
            "Vulnerability confirmed: title sanitization preserves relative '..' directory",
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
        # Demonstrates the vulnerability: checker.py is incorrectly put in skipped
        self.assertIn(
            "checker.py",
            skipped,
            "Vulnerability confirmed: source file dropped due to substring match on binary marker",
        )
        self.assertNotIn("checker.py", files)

    def test_delimiter_collision_in_code_block(self):
        """A file with an inlined <!-- SOURCE: ... --> inside a code block causes phantom files."""
        bundle_with_delimiter = (
            "**Title:** One Page Version of documentation\n\n"
            "<!-- SOURCE: SKILL.md -->\n\n## SKILL.md\n\nDocumentation\n\n"
            "<!-- SOURCE: docs/guide.md -->\n\n## docs/guide.md\n\n```markdown\n"
            "Example comment:\n<!-- SOURCE: phantom.py -->\nCode here\n```\n"
        )
        files, _ = parse_bundle(bundle_with_delimiter)
        # Demonstrates the vulnerability: phantom.py is parsed as an independent extracted file
        self.assertIn(
            "phantom.py",
            files,
            "Vulnerability confirmed: in-band delimiter causes file boundary splitting",
        )


if __name__ == "__main__":
    unittest.main()
