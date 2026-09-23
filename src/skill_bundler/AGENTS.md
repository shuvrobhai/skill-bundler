# skill_bundler package

## Overview

This is the whole tool. It turns a skill directory into one Markdown bundle, and turns a bundle back into files on disk. `cli.py` only wires `argparse` to these modules, so all the real logic sits in `bundler.py`, `unpacker.py`, and `indexer.py`. Nothing here imports outside the standard library.

## Key files

| File | Owns |
|---|---|
| `constants.py` | Centralized format tokens, markers, title prefixes, regex patterns, and probe sizes |
| `frontmatter.py` | Strict YAML frontmatter parsing, horizontal rule preservation, and multiline block folding |
| `bundler.py` | Pack side: Structure Map tree, inlining text files, domain validation (consumed by indexer) |
| `unpacker.py` | Unpack side: bundle parsing, path safety, collision guard, writing files to disk |
| `indexer.py` | Index side: skill discovery with recursive pruning, Skill Index table, Collection Bundle text |
| `cli.py` | The `argparse` parser, the `pack`, `unpack`, and `index` handlers, and every exit |
| `clipboard.py` | The OS clipboard adapter: raises `ClipboardError` on failure (strictly no `sys.exit`) |
| `__main__.py` | Module execution entry point for python -m skill_bundler |
| `__init__.py` | The public surface, re-exported through `__all__` |

## Conventions

- Standard library only. If you are reaching for a package, reach for the standard library first.
- Domain modules never call `sys.exit`. They raise `UnpackError`, `ValueError`, or `ClipboardError`, and `cli.py` decides how to fail.
- Private helpers take a leading underscore, as in `_tree_body`, `_code_fence`, `_get_clipboard_command`.
- When you add a module level function other code should use, add it to `__all__` in `__init__.py` too.

## Gotchas

The bundle format is a contract between the two modules. `bundler.py` writes it and `unpacker.py` reads it, so these exact strings have to keep matching:

- `**Title:** One Page Version of <title>` is how the unpacker names the default output directory.
- `<!-- SOURCE: <relative_path> -->` opens every file section. `<!-- SOURCE: SKILL.md -->` is the marker that proves a bundle is genuine, and unpacking refuses a bundle without it.
- `_binary file — not inlined_` marks a skipped file. The unpacker notes it and writes nothing.
- Code fences widen to `max(3, longest backtick run + 1)` so inlined content that contains backticks survives the trip.

`tests/test_unpacker.py::test_round_trip_pack_and_unpack` is the safety net for all of the above. Run it after touching either module. When the two sides drift, that test is what catches it.

A Collection Bundle holds `SKILL.md` bodies only, and it never contains the exact `<!-- SOURCE: SKILL.md -->` marker, so `unpack` refuses it as input. A `SKILL.md` sitting directly in a Collection is never included, which keeps that marker out.

Tests import `skill_bundler`, so run `pip install -e .` first, or prefix the command with `PYTHONPATH=src`.

## Related specs

- `docs/adr/0001-subcommand-cli-architecture.md`: why `pack` and `unpack` exist with a backward compatible default
- `docs/adr/0002-safe-overwrite-guard-on-unpack.md`: the `--force` collision guard
- `docs/adr/0003-strict-bundle-validation-and-safety.md`: validate everything before writing, and the path traversal guard
- `docs/adr/0004-collection-bundle-contract.md`: the Collection Bundle contract, inlines SKILL.md only, and unpack rejection
- `docs/adr/0005-bundle-delimiter-integrity-and-title-sanitization.md`: delimiter integrity, non destructive parsing, and title sanitization
- `docs/specs/0001-index-command.md`: specification for bundling whole collections into a single document
- `docs/specs/0002-architecture-and-contract-corrections.md`: contract hardening, centralized markers, and path traversal protections

_Drafted by /audit from the repo, worth a quick human pass. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
