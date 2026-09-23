"""Unit tests for the skill_bundler.cli module."""

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from skill_bundler import __version__, cli
from skill_bundler.clipboard import ClipboardError


class TestCLI(unittest.TestCase):
    """Test suite for CLI arguments, flags, and error handling."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.temp_dir.name)
        self.skill_dir = self.root_path / "my-skill"
        self.skill_dir.mkdir()
        (self.skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill\ndescription: A test skill\n---\n\n# Body\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_version_flag(self):
        with self.assertRaises(SystemExit) as ctx:
            with patch("sys.stdout", new=io.StringIO()) as fake_out:
                cli.main(["--version"])
        self.assertEqual(ctx.exception.code, 0)

    def test_pack_force_overwrites_existing_file(self):
        out_path = self.root_path / "my-skill.one-page.md"
        out_path.write_text("Old content", encoding="utf-8")

        # Without --force, it must refuse overwrite
        with self.assertRaises(SystemExit):
            cli.main(["pack", str(self.skill_dir), "-o"])
        self.assertEqual(out_path.read_text(encoding="utf-8"), "Old content")

        # With --force, it must overwrite
        cli.main(["pack", str(self.skill_dir), "-o", "--force"])
        self.assertIn("One Page Version of my-skill", out_path.read_text(encoding="utf-8"))

    def test_index_force_overwrites_existing_file(self):
        out_path = self.root_path.parent / f"{self.root_path.name}.one-page.md"
        out_path.write_text("Old index content", encoding="utf-8")

        # Without --force, it must refuse overwrite
        with self.assertRaises(SystemExit):
            cli.main(["index", str(self.root_path), "-o"])
        self.assertEqual(out_path.read_text(encoding="utf-8"), "Old index content")

        # With --force, it must overwrite
        cli.main(["index", str(self.root_path), "-o", "--force"])
        self.assertIn("Collection Bundle", out_path.read_text(encoding="utf-8"))

    def test_no_sys_exit_outside_cli(self):
        """Enforce architectural constraint: sys.exit is only permitted in cli.py."""
        pkg_dir = Path(__file__).resolve().parent.parent / "src" / "skill_bundler"
        offenders = []
        for file_path in pkg_dir.glob("*.py"):
            if file_path.name == "cli.py":
                continue
            content = file_path.read_text(encoding="utf-8")
            if "sys.exit" in content:
                offenders.append(file_path.name)
        self.assertEqual(
            offenders,
            [],
            f"sys.exit found outside cli.py in: {offenders}",
        )


if __name__ == "__main__":
    unittest.main()
