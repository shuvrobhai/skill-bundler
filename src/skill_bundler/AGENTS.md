# skill_bundler package

## Overview

This is the whole tool. It turns a skill directory into one Markdown bundle, and turns a bundle back into files on disk. `cli.py` only wires `argparse` to these modules, so all the real logic sits in `bundler.py` and `unpacker.py`. Nothing here imports outside the standard library.

## Key files

| File | Owns |
|---|---|
| `bundler.py` | Pack side: SKILL.md frontmatter parsing, the Structure Map tree, inlining text files, `validate_output` |
| `unpacker.py` | Unpack side: bundle parsing, path safety, the collision guard, writing files to disk |
| `cli.py` | The `argparse` parser, the `pack` and `unpack` handlers, and every exit |
| `clipboard.py` | The OS clipboard adapter: `pbcopy`/`pbpaste` on macOS, `wl-copy`/`xclip`/`xsel` on Linux |
| `__main__.py` | Module execution entry point for python -m skill_bundler |
| `__init__.py` | The public surface, re-exported through `__all__` |

## Conventions

- Standard library only. If you are reaching for a package, reach for the standard library first.
- Domain modules never call `sys.exit`. They raise `UnpackError` or return values, and `cli.py` decides how to fail.
- Private helpers take a leading underscore, as in `_tree_body`, `_code_fence`, `_get_clipboard_command`.
- When you add a module level function other code should use, add it to `__all__` in `__init__.py` too.

## Gotchas

The bundle format is a contract between the two modules. `bundler.py` writes it and `unpacker.py` reads it, so these exact strings have to keep matching:

- `**Title:** One Page Version of <title>` is how the unpacker names the default output directory.
- `<!-- SOURCE: <relative_path> -->` opens every file section. `<!-- SOURCE: SKILL.md -->` is the marker that proves a bundle is genuine, and unpacking refuses a bundle without it.
- `_binary file — not inlined_` marks a skipped file. The unpacker notes it and writes nothing.
- Code fences widen to `max(3, longest backtick run + 1)` so inlined content that contains backticks survives the trip.
- `validate_output` calls `sys.exit` when a check fails. That makes it CLI only, so never call it from library code or from a test.

`tests/test_unpacker.py::test_round_trip_pack_and_unpack` is the safety net for all of the above. Run it after touching either module. When the two sides drift, that test is what catches it.

Tests import `skill_bundler`, so run `pip install -e .` first, or prefix the command with `PYTHONPATH=src`.

## Related specs

- `docs/adr/0001-subcommand-cli-architecture.md`: why `pack` and `unpack` exist with a backward compatible default
- `docs/adr/0002-safe-overwrite-guard-on-unpack.md`: the `--force` collision guard
- `docs/adr/0003-strict-bundle-validation-and-safety.md`: validate everything before writing, and the path traversal guard
- `docs/adr/0004-collection-bundle-contract.md`: the Collection Bundle contract, inlines SKILL.md only, and unpack rejection
- `docs/specs/0001-index-command.md`: specification for bundling whole collections into a single document

_Drafted by /audit from the repo, worth a quick human pass. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
