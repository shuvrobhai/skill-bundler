"""Unit tests for the skill_bundler.indexer module."""

import tempfile
import unittest
from pathlib import Path

from skill_bundler import cli
from skill_bundler.indexer import build_collection_document, discover_skills


def _write_skill(parent: Path, dirname: str, name=None, description=None, body=None):
    """Create one skill dir with SKILL.md under parent, return its path."""
    skill_dir = parent / dirname
    skill_dir.mkdir(parents=True, exist_ok=True)
    if name is None and description is None:
        text = body or "# Plain skill\nNo frontmatter here.\n"
    else:
        text = (
            "---\n"
            f'name: "{name}"\n'
            f'description: "{description}"\n'
            "---\n\n" + (body or "# Body\nContent here.\n")
        )
    (skill_dir / "SKILL.md").write_text(text, encoding="utf-8")
    return skill_dir


class TestIndexer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.collection_dir = Path(self.temp_dir.name) / "skills"
        self.collection_dir.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_three_skills_produce_three_rows_and_sections(self):
        _write_skill(self.collection_dir, "aaa", "aaa", "First skill")
        _write_skill(self.collection_dir, "bbb", "bbb", "Second skill")
        _write_skill(self.collection_dir, "ccc", "ccc", "Third skill")

        skills, _skipped = discover_skills(self.collection_dir)
        document = build_collection_document(self.collection_dir, skills)

        rows = [line for line in document.splitlines() if "/SKILL.md |" in line]
        self.assertEqual(len(rows), 3)
        self.assertEqual(document.count("<!-- SOURCE:"), 3)

    def test_skills_sort_case_insensitively_with_matching_section_order(self):
        _write_skill(self.collection_dir, "zeta")
        _write_skill(self.collection_dir, "Alpha")
        _write_skill(self.collection_dir, "beta")

        skills, _skipped = discover_skills(self.collection_dir)
        self.assertEqual([entry.name for entry in skills], ["Alpha", "beta", "zeta"])

        document = build_collection_document(self.collection_dir, skills)
        index_positions = [
            document.index(f"| {name} |") for name in ["Alpha", "beta", "zeta"]
        ]
        section_positions = [
            document.index(f"## {name}") for name in ["Alpha", "beta", "zeta"]
        ]
        self.assertEqual(index_positions, sorted(index_positions))
        self.assertEqual(section_positions, sorted(section_positions))

    def test_dir_without_skill_md_is_skipped_and_counted(self):
        _write_skill(self.collection_dir, "real", "real", "A real skill")
        (self.collection_dir / "empty").mkdir()

        skills, skipped = discover_skills(self.collection_dir)
        self.assertEqual(len(skills), 1)
        self.assertEqual(skipped, ["empty"])

    def test_empty_collection_raises_and_writes_nothing(self):
        skills, _skipped = discover_skills(self.collection_dir)
        self.assertEqual(skills, [])
        with self.assertRaises(ValueError):
            build_collection_document(self.collection_dir, skills)

        with self.assertRaises(SystemExit):
            cli.main(["index", str(self.collection_dir), "-o"])
        out_path = self.collection_dir.parent / "skills.one-page.md"
        self.assertFalse(out_path.exists())

    def test_root_skill_md_is_ignored_and_marker_stays_absent(self):
        (self.collection_dir / "SKILL.md").write_text(
            "# Root file\nNot a skill in this collection.\n", encoding="utf-8"
        )
        _write_skill(self.collection_dir, "solo", "solo", "Only skill")

        skills, _skipped = discover_skills(self.collection_dir)
        self.assertEqual([entry.name for entry in skills], ["solo"])

        document = build_collection_document(self.collection_dir, skills)
        self.assertNotIn("<!-- SOURCE: SKILL.md -->", document)

    def test_long_description_truncates_and_pipe_escapes(self):
        _write_skill(self.collection_dir, "long", "long", "x" * 100)
        _write_skill(self.collection_dir, "piped", "piped", "a | b")

        skills, _skipped = discover_skills(self.collection_dir)
        document = build_collection_document(self.collection_dir, skills)

        self.assertIn("x" * 80 + "…", document)
        self.assertNotIn("x" * 81, document)
        self.assertIn("a \\| b", document)

    def test_missing_frontmatter_falls_back_to_dir_name(self):
        _write_skill(self.collection_dir, "plain")

        skills, _skipped = discover_skills(self.collection_dir)
        self.assertEqual([entry.name for entry in skills], ["plain"])

        document = build_collection_document(self.collection_dir, skills)
        self.assertIn("| plain |", document)
        self.assertIn("## plain", document)

    def test_nested_skill_needs_recursive_flag(self):
        _write_skill(self.collection_dir / "group", "nested", "nested", "Deep skill")

        default_skills, _s1 = discover_skills(self.collection_dir)
        self.assertEqual(default_skills, [])

        recursive_skills, _s2 = discover_skills(self.collection_dir, True)
        self.assertEqual([entry.name for entry in recursive_skills], ["nested"])
        self.assertEqual(
            recursive_skills[0].relative_path, "group/nested/SKILL.md"
        )

    def test_hidden_and_cache_dirs_are_silently_skipped(self):
        _write_skill(self.collection_dir / ".secret", "ghost", "ghost", "Hidden")
        _write_skill(
            self.collection_dir / "__pycache__", "cached", "cached", "Cached"
        )
        _write_skill(self.collection_dir, "real", "real", "Visible skill")
        (self.collection_dir / "empty").mkdir()

        skills, skipped = discover_skills(self.collection_dir)
        self.assertEqual([entry.name for entry in skills], ["real"])
        self.assertEqual(skipped, ["empty"])

    def test_output_flag_writes_file_and_refuses_overwrite(self):
        _write_skill(self.collection_dir, "solo", "solo", "Only skill")
        out_path = self.collection_dir.parent / "skills.one-page.md"

        cli.main(["index", str(self.collection_dir), "-o"])
        self.assertTrue(out_path.is_file())
        content = out_path.read_text(encoding="utf-8")
        self.assertIn("Collection Bundle", content)
        self.assertIn("solo/SKILL.md", content)

        with self.assertRaises(SystemExit):
            cli.main(["index", str(self.collection_dir), "-o"])


if __name__ == "__main__":
    unittest.main()
