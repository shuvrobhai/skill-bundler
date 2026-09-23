"""Command-line interface for skill-bundler (pack and unpack subcommands)."""

import argparse
import sys
from pathlib import Path

from skill_bundler.bundler import (
    build_bundle_document,
    collect_skill_files,
    parse_skill,
)
from skill_bundler.clipboard import copy_to_clipboard, paste_from_clipboard
from skill_bundler.indexer import build_collection_document, discover_skills
from skill_bundler.unpacker import (
    UnpackError,
    extract_skill_title,
    unpack_bundle,
)


def _deliver_document(
    document: str,
    out_path: Path,
    args: argparse.Namespace,
    written_lines: list[str],
    copied_lines: list[str],
) -> None:
    if args.output:
        if out_path.exists():
            sys.exit(f"Error: '{out_path}' already exists. Move or delete it first.")
        out_path.write_text(document, encoding="utf-8")
        for line in written_lines:
            print(line)
    elif args.terminal:
        print(document)
    else:
        # Default behavior: copy to clipboard
        copy_to_clipboard(document)
        for line in copied_lines:
            print(line)


def _handle_pack(args: argparse.Namespace) -> None:
    skill_dir = args.skill_dir.resolve()
    skill_md_path = skill_dir / "SKILL.md"

    if not skill_dir.is_dir():
        sys.exit(f"Error: '{skill_dir}' is not a directory.")
    if not skill_md_path.is_file():
        sys.exit(f"Error: '{skill_md_path}' does not exist (SKILL.md is required).")

    files = collect_skill_files(skill_dir)
    document, inlined_count, skipped_files = build_bundle_document(
        skill_dir, skill_md_path, files
    )

    _, _, skill_body = parse_skill(skill_md_path)
    if "Skill's Structure Map" not in document:
        sys.exit("Validation failed: structure map is missing.")
    if skill_body and skill_body.strip()[:200] not in document:
        sys.exit("Validation failed: SKILL.md body is missing from output.")
    if inlined_count + len(skipped_files) > 0:
        expected_comments = inlined_count + len(skipped_files) + 1
        if document.count("<!-- SOURCE:") < expected_comments:
            sys.exit("Validation failed: not all source separators made it into output.")

    out_path = skill_dir.parent / f"{skill_dir.name}.one-page.md"
    written_lines = [
        f"✅ Wrote {out_path}",
        f"   Inlined: {inlined_count} text file(s)",
    ]
    copied_lines = [f"📋 Copied to clipboard ({inlined_count} files inlined)"]
    if skipped_files:
        skipped_lines = [f"   Skipped: {len(skipped_files)} binary/undecodable file(s)"]
        skipped_lines.extend(f"     - {relative_path}" for relative_path in skipped_files)
        written_lines.extend(skipped_lines)
        copied_lines.extend(skipped_lines)
    _deliver_document(document, out_path, args, written_lines, copied_lines)


def _handle_unpack(args: argparse.Namespace) -> None:
    # 1. Obtain bundle text from clipboard or file
    if args.clipboard:
        bundle_text = paste_from_clipboard()
        if not bundle_text or not bundle_text.strip():
            sys.exit("Error: Clipboard is empty.")
    elif args.bundle_file:
        bundle_path = args.bundle_file.resolve()
        if not bundle_path.is_file():
            sys.exit(f"Error: Bundle file '{bundle_path}' does not exist.")
        bundle_text = bundle_path.read_text(encoding="utf-8")
    else:
        sys.exit("Error: Specify a bundle file or use -c / --clipboard to unpack.")

    # 2. Determine target destination directory
    if args.destination:
        target_dir = args.destination.resolve()
    else:
        skill_title = extract_skill_title(bundle_text)
        target_dir = Path.cwd() / skill_title

    # 3. Unpack
    try:
        unpacked_count, skipped_files = unpack_bundle(
            bundle_text, target_dir, should_overwrite=args.force
        )
    except UnpackError as err:
        sys.exit(f"Error: {err}")

    print(f"🎉 Successfully unpacked skill to: {target_dir}")
    print(f"   Extracted: {unpacked_count} file(s)")
    if skipped_files:
        print(f"   Skipped binary reference(s): {len(skipped_files)}")
        for relative_path in skipped_files:
            print(f"     - {relative_path}")


def _handle_index(args: argparse.Namespace) -> None:
    collection_dir = args.collection_dir.resolve()

    if not collection_dir.is_dir():
        sys.exit(f"Error: '{collection_dir}' is not a directory.")

    skills, skipped_dir_names = discover_skills(
        collection_dir, args.recursive
    )
    if not skills:
        sys.exit(f"Error: No skills found in '{collection_dir}'.")

    document = build_collection_document(collection_dir, skills)
    indexed_count = len(skills)
    skipped_count = len(skipped_dir_names)

    out_path = collection_dir.parent / f"{collection_dir.name}.one-page.md"
    _deliver_document(
        document,
        out_path,
        args,
        [
            f"✅ {indexed_count} skills indexed, "
            f"{skipped_count} folders skipped → {out_path}"
        ],
        [
            f"📋 Copied to clipboard "
            f"({indexed_count} skills indexed, {skipped_count} folders skipped)"
        ],
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skill-bundler",
        description="Bundle an AI agent skill directory into Markdown, or unpack a bundle back into files.",
    )
    subparsers = parser.add_subparsers(dest="subcommand")

    # 'pack' subcommand
    pack_parser = subparsers.add_parser(
        "pack",
        help="Bundle a skill directory into a self-contained Markdown file.",
    )
    pack_parser.add_argument(
        "skill_dir",
        type=Path,
        help="Path to the skill directory containing SKILL.md",
    )
    pack_group = pack_parser.add_mutually_exclusive_group()
    pack_group.add_argument(
        "-c",
        "--clipboard",
        action="store_true",
        help="Copy to clipboard (default)",
    )
    pack_group.add_argument(
        "-t",
        "--terminal",
        action="store_true",
        help="Print to terminal (stdout)",
    )
    pack_group.add_argument(
        "-o",
        "--output",
        action="store_true",
        help="Write to <skill>.one-page.md file",
    )

    # 'unpack' subcommand
    unpack_parser = subparsers.add_parser(
        "unpack",
        help="Unpack a Markdown bundle back into a skill directory.",
    )
    unpack_parser.add_argument(
        "bundle_file",
        type=Path,
        nargs="?",
        default=None,
        help="Path to the Markdown bundle file to unpack",
    )
    unpack_parser.add_argument(
        "-c",
        "--clipboard",
        action="store_true",
        help="Read bundle directly from system clipboard",
    )
    unpack_parser.add_argument(
        "-d",
        "--destination",
        type=Path,
        default=None,
        help="Destination directory for unpacked skill (defaults to ./<skill-title>/)",
    )
    unpack_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite existing files in destination directory",
    )

    # 'index' subcommand
    index_parser = subparsers.add_parser(
        "index",
        help="Bundle a collection directory into a single Markdown document.",
    )
    index_parser.add_argument(
        "collection_dir",
        type=Path,
        help="Path to the collection directory holding skills",
    )
    index_parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Include skills nested below immediate children",
    )
    index_group = index_parser.add_mutually_exclusive_group()
    index_group.add_argument(
        "-c",
        "--clipboard",
        action="store_true",
        help="Copy to clipboard (default)",
    )
    index_group.add_argument(
        "-t",
        "--terminal",
        action="store_true",
        help="Print to terminal (stdout)",
    )
    index_group.add_argument(
        "-o",
        "--output",
        action="store_true",
        help="Write to <collection>.one-page.md file",
    )

    return parser


def main(argv=None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    # Backward compatibility: if first arg is not a known subcommand or help flag, default to 'pack'
    if argv and argv[0] not in ("pack", "unpack", "index", "-h", "--help", "-v", "--version"):
        argv = ["pack"] + argv

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.subcommand == "pack":
        _handle_pack(args)
    elif args.subcommand == "unpack":
        _handle_unpack(args)
    elif args.subcommand == "index":
        _handle_index(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
