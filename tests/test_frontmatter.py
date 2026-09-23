"""Unit tests for the skill_bundler.frontmatter module."""

import unittest
from skill_bundler.frontmatter import parse_skill_text


class TestFrontmatter(unittest.TestCase):
    """Test suite for frontmatter parsing and YAML multiline folding."""

    def test_basic_frontmatter(self):
        text = (
            "---\n"
            "name: test-skill\n"
            "description: A simple test skill\n"
            "---\n\n"
            "# Body\n"
            "Body content.\n"
        )
        name, description, body = parse_skill_text(text)
        self.assertEqual(name, "test-skill")
        self.assertEqual(description, "A simple test skill")
        self.assertEqual(body, "# Body\nBody content.\n")

    def test_frontmatter_with_quotes(self):
        text = (
            "---\n"
            'name: "quoted-skill"\n'
            'description: "Quoted description"\n'
            "---\n\n"
            "Body text\n"
        )
        name, description, body = parse_skill_text(text)
        self.assertEqual(name, "quoted-skill")
        self.assertEqual(description, "Quoted description")
        self.assertEqual(body, "Body text\n")

    def test_no_frontmatter(self):
        text = "# Just markdown\nNo frontmatter delimiters at all.\n"
        name, description, body = parse_skill_text(text)
        self.assertEqual(name, "")
        self.assertEqual(description, "")
        self.assertEqual(body, text)

    def test_extra_horizontal_rules_in_body_preserved(self):
        text = (
            "---\n"
            "name: hr-skill\n"
            "description: Testing horizontal rules\n"
            "---\n\n"
            "# Section 1\n\n"
            "---\n\n"
            "# Section 2\n\n"
            "---\n\n"
            "End of document.\n"
        )
        name, description, body = parse_skill_text(text)
        self.assertEqual(name, "hr-skill")
        self.assertEqual(description, "Testing horizontal rules")
        self.assertIn("# Section 1", body)
        self.assertIn("# Section 2", body)
        self.assertIn("End of document.", body)
        self.assertEqual(body.count("---"), 2)

    def test_multiline_folded_description(self):
        text = (
            "---\n"
            "name: folded-skill\n"
            "description: >\n"
            "  This is a multiline description\n"
            "  that spans across multiple lines\n"
            "  and should be folded into one string.\n"
            "---\n\n"
            "# Body\n"
        )
        name, description, body = parse_skill_text(text)
        self.assertEqual(name, "folded-skill")
        self.assertEqual(
            description,
            "This is a multiline description that spans across multiple lines and should be folded into one string.",
        )
        self.assertEqual(body, "# Body\n")

    def test_multiline_literal_description(self):
        text = (
            "---\n"
            "name: literal-skill\n"
            "description: |\n"
            "  Line 1 of description\n"
            "  Line 2 of description\n"
            "---\n\n"
            "# Body\n"
        )
        name, description, body = parse_skill_text(text)
        self.assertEqual(name, "literal-skill")
        self.assertEqual(
            description,
            "Line 1 of description\nLine 2 of description",
        )
        self.assertEqual(body, "# Body\n")


if __name__ == "__main__":
    unittest.main()
