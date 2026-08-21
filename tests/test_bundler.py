"""Unit tests for the skill_bundler.bundler module."""

import tempfile
import unittest
from pathlib import Path

from skill_bundler.bundler import (
    build_bundle_document,
    collect_skill_files,
    directory_tree,
    parse_skill,
    validate_output,
)


class TestBundler(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.skill_dir = Path(self.temp_dir.name) / "my-test-skill"
        self.skill_dir.mkdir()

        # Create SKILL.md
        self.skill_md = self.skill_dir / "SKILL.md"
        self.skill_md.write_text(
            '---\nname: "my-test-skill"\ndescription: "A test skill"\n---\n\n# My Test Skill\n\nInstructions here.',
            encoding="utf-8",
        )

        # Create a helper script
        scripts_dir = self.skill_dir / "scripts"
        scripts_dir.mkdir()
        self.helper_py = scripts_dir / "helper.py"
        self.helper_py.write_text("def run():\n    print('hello world')\n", encoding="utf-8")

        # Create a nested config file
        config_dir = self.skill_dir / "config"
        config_dir.mkdir()
        self.config_yaml = config_dir / "settings.yaml"
        self.config_yaml.write_text("mode: development\nenabled: true\n", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_skill_with_frontmatter(self):
        name, description, body = parse_skill(self.skill_md)
        self.assertEqual(name, "my-test-skill")
        self.assertEqual(description, "A test skill")
        self.assertIn("# My Test Skill", body)

    def test_parse_skill_without_frontmatter(self):
        plain_md = self.skill_dir / "PLAIN.md"
        plain_md.write_text("# Plain Skill\nNo frontmatter here.", encoding="utf-8")
        name, description, body = parse_skill(plain_md)
        self.assertEqual(name, "")
        self.assertEqual(description, "")
        self.assertEqual(body, "# Plain Skill\nNo frontmatter here.")

    def test_collect_skill_files(self):
        # Create hidden file and pycache file which should be excluded
        hidden_file = self.skill_dir / ".hidden"
        hidden_file.write_text("secret", encoding="utf-8")

        pycache_dir = self.skill_dir / "__pycache__"
        pycache_dir.mkdir()
        (pycache_dir / "cache.pyc").write_bytes(b"\x00\x01\x02")

        files = collect_skill_files(self.skill_dir)
        file_names = [f.name for f in files]
        self.assertIn("helper.py", file_names)
        self.assertIn("settings.yaml", file_names)
        self.assertNotIn("SKILL.md", file_names)
        self.assertNotIn(".hidden", file_names)
        self.assertNotIn("cache.pyc", file_names)

    def test_directory_tree_structure(self):
        tree = directory_tree(self.skill_dir)
        self.assertIn("my-test-skill", tree)
        self.assertIn("SKILL.md", tree)
        self.assertIn("scripts", tree)
        self.assertIn("helper.py", tree)
        self.assertIn("config", tree)
        self.assertIn("settings.yaml", tree)

    def test_build_bundle_document(self):
        files = collect_skill_files(self.skill_dir)
        document, inlined_count, skipped_files = build_bundle_document(
            self.skill_dir, self.skill_md, files
        )

        self.assertEqual(inlined_count, 2)
        self.assertEqual(len(skipped_files), 0)
        self.assertIn("**Title:** One Page Version of my-test-skill", document)
        self.assertIn("# Skill's Structure Map", document)
        self.assertIn("<!-- SOURCE: SKILL.md -->", document)
        self.assertIn("<!-- SOURCE: scripts/helper.py -->", document)
        self.assertIn("<!-- SOURCE: config/settings.yaml -->", document)
        self.assertIn("def run():", document)

    def test_binary_file_skipped(self):
        binary_file = self.skill_dir / "data.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03\x04\x05")

        files = collect_skill_files(self.skill_dir)
        document, inlined_count, skipped_files = build_bundle_document(
            self.skill_dir, self.skill_md, files
        )

        self.assertIn("data.bin", skipped_files)
        self.assertIn("_binary file — not inlined_", document)


if __name__ == "__main__":
    unittest.main()
