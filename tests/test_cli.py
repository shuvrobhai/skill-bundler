"""Unit tests for the bundium.cli module."""

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bundium import __version__, cli
from bundium.clipboard import ClipboardError


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

    def test_bare_path_defaults_to_pack_terminal(self):
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            cli.main([str(self.skill_dir), "-t"])
        output = fake_out.getvalue()
        self.assertIn("**Title:** One Page Version of my-skill", output)
        self.assertIn("<!-- SOURCE: SKILL.md -->", output)

    def test_unpack_file_with_destination(self):
        bundle_file = self.root_path / "skill.one-page.md"
        bundle_file.write_text(
            "**Title:** One Page Version of unpacked-test\n\n"
            "<!-- SOURCE: SKILL.md -->\n\n## SKILL.md\n\n# Unpacked Content\n",
            encoding="utf-8",
        )
        dest_dir = self.root_path / "custom-dest"
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            cli.main(["unpack", str(bundle_file), "-d", str(dest_dir)])
        self.assertTrue((dest_dir / "SKILL.md").is_file())
        self.assertEqual(
            (dest_dir / "SKILL.md").read_text(encoding="utf-8"),
            "# Unpacked Content\n",
        )
        self.assertIn("Successfully unpacked skill to:", fake_out.getvalue())

    def test_unpack_collision_refuses_without_force(self):
        bundle_file = self.root_path / "collision.one-page.md"
        bundle_file.write_text(
            "**Title:** One Page Version of clash\n\n"
            "<!-- SOURCE: SKILL.md -->\n\n## SKILL.md\n\n# New\n",
            encoding="utf-8",
        )
        dest_dir = self.root_path / "clash-dir"
        dest_dir.mkdir()
        (dest_dir / "SKILL.md").write_text("# Existing\n", encoding="utf-8")

        # Must exit on collision without force
        with self.assertRaises(SystemExit) as ctx:
            cli.main(["unpack", str(bundle_file), "-d", str(dest_dir)])
        self.assertIn("Use --force", str(ctx.exception))
        self.assertEqual((dest_dir / "SKILL.md").read_text(encoding="utf-8"), "# Existing\n")

        # Must overwrite with --force
        with patch("sys.stdout", new=io.StringIO()):
            cli.main(["unpack", str(bundle_file), "-d", str(dest_dir), "--force"])
        self.assertEqual((dest_dir / "SKILL.md").read_text(encoding="utf-8"), "# New\n")

    @patch("bundium.cli.paste_from_clipboard", return_value="")
    def test_unpack_clipboard_empty_exits(self, mock_paste):
        with self.assertRaises(SystemExit) as ctx:
            cli.main(["unpack", "-c"])
        self.assertIn("Clipboard is empty", str(ctx.exception))

    def test_no_sys_exit_outside_cli(self):
        """Enforce architectural constraint: sys.exit is only permitted in cli.py."""
        pkg_dir = Path(__file__).resolve().parent.parent / "src" / "bundium"
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
