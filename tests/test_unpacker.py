"""Unit tests for the skill_bundler.unpacker module."""

import tempfile
import unittest
from pathlib import Path

from skill_bundler.bundler import build_bundle_document, collect_skill_files
from skill_bundler.unpacker import (
    UnpackError,
    extract_skill_title,
    is_safe_relative_path,
    parse_bundle,
    unpack_bundle,
)


class TestUnpacker(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.temp_dir.name)

        # Create sample skill directory
        self.source_skill = self.root_path / "original-skill"
        self.source_skill.mkdir()

        self.skill_md = self.source_skill / "SKILL.md"
        self.skill_md.write_text(
            '---\nname: "original-skill"\ndescription: "Original sample skill"\n---\n\n# Original Skill Body\n\nContent here.\n',
            encoding="utf-8",
        )

        scripts_dir = self.source_skill / "scripts"
        scripts_dir.mkdir()
        self.script_file = scripts_dir / "worker.py"
        self.script_file.write_text(
            'def do_work():\n    return "done"\n',
            encoding="utf-8",
        )

        nested_dir = self.source_skill / "nested" / "deep"
        nested_dir.mkdir(parents=True)
        self.nested_file = nested_dir / "note.txt"
        self.nested_file.write_text("Deeply nested note content.\n", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_extract_skill_title(self):
        bundle_text = "**Title:** One Page Version of awesome-agent\n**Source:** file:///path\n"
        self.assertEqual(extract_skill_title(bundle_text), "awesome-agent")

        empty_text = "No title header here"
        self.assertEqual(extract_skill_title(empty_text), "unpacked-skill")

    def test_path_traversal_safety(self):
        target_dir = self.root_path / "dest"
        target_dir.mkdir()

        self.assertTrue(is_safe_relative_path(target_dir, "valid/path/file.py"))
        self.assertTrue(is_safe_relative_path(target_dir, "file.txt"))
        self.assertFalse(is_safe_relative_path(target_dir, "../outside.py"))
        self.assertFalse(is_safe_relative_path(target_dir, "../../evil.sh"))
        self.assertFalse(is_safe_relative_path(target_dir, "/absolute/path/file.py"))

    def test_round_trip_pack_and_unpack(self):
        """Bundle a directory and unpack it; verify all files and contents match identically."""
        files = collect_skill_files(self.source_skill)
        bundle_document, _, _ = build_bundle_document(
            self.source_skill, self.skill_md, files
        )

        dest_dir = self.root_path / "unpacked-destination"
        unpacked_count, skipped_files = unpack_bundle(bundle_document, dest_dir)

        self.assertEqual(unpacked_count, 3)
        self.assertEqual(len(skipped_files), 0)

        # Check all files exist in destination with matching content
        self.assertTrue((dest_dir / "SKILL.md").is_file())
        self.assertTrue((dest_dir / "scripts" / "worker.py").is_file())
        self.assertTrue((dest_dir / "nested" / "deep" / "note.txt").is_file())

        self.assertEqual(
            (dest_dir / "SKILL.md").read_text(encoding="utf-8"),
            self.skill_md.read_text(encoding="utf-8"),
        )
        self.assertEqual(
            (dest_dir / "scripts" / "worker.py").read_text(encoding="utf-8"),
            self.script_file.read_text(encoding="utf-8"),
        )
        self.assertEqual(
            (dest_dir / "nested" / "deep" / "note.txt").read_text(encoding="utf-8"),
            self.nested_file.read_text(encoding="utf-8"),
        )

    def test_collision_guard_without_force(self):
        """Unpacking into existing directory fails unless should_overwrite=True."""
        files = collect_skill_files(self.source_skill)
        bundle_document, _, _ = build_bundle_document(
            self.source_skill, self.skill_md, files
        )

        dest_dir = self.root_path / "collision-test"
        dest_dir.mkdir()
        (dest_dir / "SKILL.md").write_text("Pre-existing content", encoding="utf-8")

        # Must raise UnpackError without should_overwrite
        with self.assertRaises(UnpackError) as ctx:
            unpack_bundle(bundle_document, dest_dir, should_overwrite=False)
        self.assertIn("Use --force", str(ctx.exception))

        # Must succeed with should_overwrite=True
        unpacked_count, _ = unpack_bundle(
            bundle_document, dest_dir, should_overwrite=True
        )
        self.assertEqual(unpacked_count, 3)
        self.assertEqual(
            (dest_dir / "SKILL.md").read_text(encoding="utf-8"),
            self.skill_md.read_text(encoding="utf-8"),
        )

        # Backwards compatibility check: force=True also works
        unpacked_count_force, _ = unpack_bundle(
            bundle_document, dest_dir, force=True
        )
        self.assertEqual(unpacked_count_force, 3)

    def test_reject_unsafe_path_traversal(self):
        """Unpack must reject bundles containing path traversal attempts."""
        malicious_bundle = (
            "**Title:** One Page Version of exploit\n\n"
            "<!-- SOURCE: SKILL.md -->\n\n## SKILL.md\n\nBody\n\n"
            "<!-- SOURCE: ../evil.py -->\n\n## ../evil.py\n\n```python\nprint('pwn')\n```\n"
        )
        dest_dir = self.root_path / "safe-dir"
        with self.assertRaises(UnpackError) as ctx:
            unpack_bundle(malicious_bundle, dest_dir)
        self.assertIn("Security violation", str(ctx.exception))

    def test_reject_invalid_bundle(self):
        invalid_text = "This is just random text with no skill markers."
        dest_dir = self.root_path / "invalid-test"
        with self.assertRaises(UnpackError) as ctx:
            unpack_bundle(invalid_text, dest_dir)
        self.assertIn("missing '<!-- SOURCE: SKILL.md -->'", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
