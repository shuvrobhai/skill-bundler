# 0000 — Bundium tool spec

**Status:** Accepted
**Covers:** v0.2.1

This is the whole tool on one page: what it does, the exact CLI surface, the document contracts, and the conventions the code follows. Feature history lives in the design decisions table in [architecture-and-walkthrough.md](../architecture-and-walkthrough.md) and spec 0001; this file consolidates them and the code never drifts from it without a spec update or a new design decision.

Related: spec 0001 (`index`).

## 1. What the tool is

`bundium` packs a folder of Markdown files — typically an AI agent Skill topped by `SKILL.md` — into a single self-contained Markdown Bundle for pasting into LLM sessions, unpacks a Bundle back into a directory, and surveys a whole Collection (a directory of Skills) into one Collection Bundle. Standard library only, zero runtime dependencies, Python 3.9+, `src/` layout, installed via `uv sync`.

## 2. CLI surface

```
bundium pack <skill-dir> [-c | -t | -o]
bundium unpack [bundle-file] [-c] [-d <dir>] [-f]
bundium index <collection-dir> [-r] [-c | -t | -o]
```

- A bare path with no subcommand defaults to `pack` (backward compatible). `index` is on the subcommand whitelist so the shim never rewrites it.
- Delivery Target flags mirror each other and stay mutually exclusive: clipboard is the default (`-c`), `-t` prints to stdout, `-o` writes a `.one-page.md` file next to the source directory.
- `-o` refuses to overwrite an existing file (exit 1); there is no force flag on the write path.
- `pack` requires `SKILL.md` at the top of `<skill-dir>` and exits 1 without it.
- `unpack` needs a source: a bundle file or `-c` for the clipboard (exit 1 on an empty clipboard or a missing file). Destination defaults to `./<skill-title>/`, derived from the Bundle title; `-d` overrides it.
- `unpack` aborts on any filename collision unless `--force` / `-f` is passed.
- `index` finds Skills (directories directly containing `SKILL.md`) among the immediate children by default, the whole tree with `-r` / `--recursive`. Hidden entries and `__pycache__` are skipped at every level; the Collection directory itself may be hidden. Directories without `SKILL.md` are skipped and counted. A `SKILL.md` sitting directly in the Collection is never included. Zero Skills found is an error (exit 1, nothing written).
- `cli.py` owns every `sys.exit`. Domain modules raise (`UnpackError`, `ValueError`, `ClipboardError`) or return values.

## 3. Single Skill Bundle format

Written by `bundle_format.serialize`, read by `bundle_format.deserialize`. The exact strings are a contract; `tests/test_unpacker.py::test_round_trip_pack_and_unpack` guards it.

```
**Title:** One Page Version of <title>
**Source:** [<uri>](<uri>)

---

# Skill's Structure Map

```text
<ascii tree, SKILL.md first>
```

---

<!-- SOURCE: SKILL.md -->

## SKILL.md

<full SKILL.md text, frontmatter included>

<!-- SOURCE: <relative_path> -->

## <relative_path>

<fenced file content, language tagged by extension>
... or `_binary file — not inlined_` for binary/undecodable files
```

- `<title>` comes from the `SKILL.md` frontmatter `name:`, falling back to the directory name. `<uri>` is the resolved `SKILL.md` path as a file URI.
- Code fences widen to `max(3, longest backtick run + 1)` so inlined content containing backticks survives the trip.
- Binary detection probes the first 8192 bytes for null bytes, falling back to UTF-8 decode; undecodable files are noted by name, never embedded.

## 4. Unpack rules

`unpack_bundle` runs three passes in order and writes nothing until all pass:

1. **Parse and validate**: the literal `<!-- SOURCE: SKILL.md -->` marker must be present (this is what proves a Bundle is genuine); every section splits on `<!-- SOURCE: <path> -->`; fenced content is extracted; a missing `SKILL.md` is an error.
2. **Path safety**: absolute paths and anything resolving outside the target directory raise `UnpackError`. Paths resolving directly to the destination directory root are rejected. Dot-only titles (`.`, `..`) and hidden-directory names fall back to the default destination directory.
3. **Collision guard**: any existing destination file aborts the run unless overwriting was explicitly allowed.

Files are written with parent directories created as needed, each ending in a newline. Binary references from the Bundle are reported, never written.

## 5. Collection Bundle format

Written by `indexer.py`. Deliberately not valid `unpack` input (see spec 0001).

```
**Title:** Collection Bundle — <collection dir name>
**Source:** [<uri>](<uri>)
**Skills:** <count>

---

# Skill Index

| Skill | Description | Path |
|---|---|---|
| <name> | <description> | <path>/SKILL.md |
...

---

<!-- SOURCE: <path>/SKILL.md -->

## <name>

<SKILL.md body, frontmatter stripped>
...
```

- The header never reuses `**Title:** One Page Version of ...`, so the two document kinds cannot be confused.
- No generation timestamp: the same Collection yields byte-identical output on every run.
- Index rows sort by Skill name, case-insensitively; section order matches. `name` falls back to the directory name when there is no frontmatter. Descriptions collapse whitespace, truncate to 80 characters with `…` appended, and escape `|` for the table cell.
- Only `SKILL.md` files are inlined, never supporting files. The document never contains the literal `<!-- SOURCE: SKILL.md -->`, which is exactly why `unpack` rejects it. Use `pack` for one Skill in full.
- Summary line on write: `✅ <n> skills indexed, <m> folders skipped → <path>`.

## 6. Clipboard

`pbcopy` / `pbpaste` on macOS (built in); `wl-copy` / `wl-paste`, `xclip`, or `xsel` on Linux (first one found on `PATH` wins); Windows is unsupported and exits with an error, as does a Linux box with no clipboard utility installed.

## 7. Module layout

| File | Owns |
|---|---|
| `constants.py` | Format tokens, markers, and probe sizes shared by bundler and unpacker |
| `bundle_format.py` | Format contract: serialization, deserialization, code fence helper |
| `frontmatter.py` | Strict YAML frontmatter parsing, horizontal rule preservation, multiline block folding |
| `bundler.py` | Pack side: file collection, Structure Map tree, delegates document assembly to `bundle_format.py` |
| `unpacker.py` | Unpack side: parsing, path safety, collision guard, disk writer |
| `indexer.py` | Index side: skill discovery with recursive pruning, Skill Index table, Collection Bundle text |
| `utils.py` | Shared path exclusion predicate consumed by `bundler.py` and `indexer.py` |
| `cli.py` | `argparse` wiring, the three handlers, the shared delivery helper, every exit |
| `clipboard.py` | OS clipboard adapter (`ClipboardError`, strictly no `sys.exit`) |
| `__init__.py` | Public surface via `__all__` (`SkillEntry`, `UnpackError`, builders, discovery, clipboard) |
| `__main__.py` | `python -m bundium` entry point |

Conventions: `snake_case` functions and variables, `PascalCase` classes, `UPPER_SNAKE_CASE` constants, `_` prefix on private helpers, booleans starting with `is_`, `has_`, `can_`, or `should_`. Public helpers are re-exported through `__all__`. Backward-compatible aliases (`directory_tree`, `unpack_bundle(force=...)`) are kept deliberately. Domain words follow `CONTEXT.md`.

## 8. Testing

`unittest`, `tests/` mirror the modules (`test_bundler.py`, `test_unpacker.py`, `test_indexer.py`, one test per rule for the index side). Run installed, or prefixed:

```
uv run python -m unittest discover -s tests
```

See [testing.md](../testing.md) for the full breakdown.

## 9. Releases

Versions in `pyproject.toml` and `bundium.__version__` together, tagged `v<version>`. Each release ships notes in `docs/releases/<version>.md` and a `CHANGELOG.md` entry (Keep a Changelog). See [deployment/README.md](../../deployment/README.md) for the full release process.