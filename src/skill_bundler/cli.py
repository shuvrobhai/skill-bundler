"""Command-line interface for skill-bundler."""

import argparse
import sys
from pathlib import Path

from skill_bundler.bundler import (
    build_bundle_document,
    collect_skill_files,
    parse_skill,
    validate_output,
)
from skill_bundler.clipboard import copy_to_clipboard


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        prog="skill-bundler",
        description="Bundle a skill directory into one self-contained Markdown file.",
    )
    parser.add_argument("skill_dir", type=Path, help="Path to the skill directory")

    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "-c",
        "--clipboard",
        action="store_true",
        help="Copy to clipboard (default)",
    )
    output_group.add_argument(
        "-t",
        "--terminal",
        action="store_true",
        help="Print to terminal (stdout)",
    )
    output_group.add_argument(
        "-o",
        "--output",
        action="store_true",
        help="Write to a <skill>.one-page.md file next to skill directory",
    )

    args = parser.parse_args(argv)

    skill_dir = args.skill_dir.resolve()
    skill_md_path = skill_dir / "SKILL.md"

    if not skill_dir.is_dir():
        sys.exit(f"Error: {skill_dir} is not a directory.")
    if not skill_md_path.is_file():
        sys.exit(f"Error: {skill_md_path} does not exist.")

    files = collect_skill_files(skill_dir)
    document, inlined_count, skipped_files = build_bundle_document(
        skill_dir, skill_md_path, files
    )

    _, _, skill_body = parse_skill(skill_md_path)
    validate_output(document, skill_body, inlined_count + len(skipped_files))

    if args.output:
        out_path = skill_dir.parent / f"{skill_dir.name}.one-page.md"
        if out_path.exists():
            sys.exit(f"Error: {out_path} already exists. Move or delete it first.")
        out_path.write_text(document, encoding="utf-8")
        print(f"✅ Wrote {out_path}")
        print(f"   Inlined: {inlined_count} text file(s)")
        if skipped_files:
            print(f"   Skipped: {len(skipped_files)} binary/undecodable file(s)")
            for relative_path in skipped_files:
                print(f"     - {relative_path}")
    elif args.terminal:
        print(document)
    else:
        # Default behavior or explicit -c: copy to clipboard
        copy_to_clipboard(document)
        print(f"📋 Copied to clipboard ({inlined_count} files inlined)")
        if skipped_files:
            print(f"   Skipped: {len(skipped_files)} binary/undecodable file(s)")
            for relative_path in skipped_files:
                print(f"     - {relative_path}")


if __name__ == "__main__":
    main()
