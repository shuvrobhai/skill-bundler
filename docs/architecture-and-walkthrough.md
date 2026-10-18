# Architecture and Walkthrough

## Table of Contents

- [Design Decisions](#design-decisions-adrs)
- [Solution Architecture](#solution-architecture)
  - [Component Architecture](#component-architecture)
  - [Runtime and Delivery Architecture](#runtime-and-delivery-architecture)
- [Application Design](#application-design)
  - [CLI Design](#cli-design)
  - [Configuration Management](#configuration-management)
- [Presentation Layer (Terminal plus Clipboard)](#presentation-layer-terminal-plus-clipboard)
- [Service Layer](#service-layer)
  - [Pack Service](#pack-service)
  - [Unpack Service](#unpack-service)
  - [Index Service](#index-service)
- [Bundle Data Model](#bundle-data-model)
- [Skill Ingestion Architecture](#skill-ingestion-architecture)
- [Security and Safety Guards](#security-and-safety-guards)
- [User Journeys Walkthrough](#user-journeys-walkthrough)

## Design Decisions (ADRs)

| Decision | Rationale |
| :--- | :--- |
| Subcommand CLI with backward-compatible default (ADR-0001) | Keeps `bundium <skill-dir>` working as `pack` while allowing `pack`, `unpack`, `index` to grow without flag collisions. Trade-off: extra routing logic in `main()` to detect bare path vs subcommand. |
| Safe overwrite guard on unpack (ADR-0002) | `unpack` aborts on collision unless `--force` is passed. Prevents accidental loss of local files. Trade-off: less convenient, requires explicit flag for overwrite. |
| Strict validation before write + path traversal guard (ADR-0003) | Parse full Bundle in memory, require `SKILL.md` marker, reject `../` escapes before touching disk. Either everything unpacks or nothing does. Trade-off: higher memory use, stricter rejection of malformed input. |
| Collection Bundle inlines `SKILL.md` only, not unpackable (ADR-0004) | Full inlining was ~713k bytes (~178k tokens) for 19 skills; `SKILL.md`-only is ~185k bytes. Survey answers "what skills exist", `pack` remains the way to get full files. Reuses missing `<!-- SOURCE: SKILL.md -->` marker to reject `unpack` for free. |
| Delimiter anchoring + title sanitization + exact binary check (ADR-0005) | Line-anchored `<!-- SOURCE: ... -->` regex plus Structure Map cross-check prevents docs that mention the marker from fragmenting. Dot-only titles (`.`, `..`) fall back to `unpacked-skill`. Exact binary-notice match prevents self-referential docs from being dropped. Preserves backward compatibility. |
| Standard library only, zero runtime dependencies | Maximizes portability (Python 3.9+) and install simplicity (`uv sync` or `pip install -e .`). Trade-off: hand-rolled frontmatter parsing and clipboard adapters instead of libraries. |
| `cli.py` owns all `sys.exit`, domain modules raise | `bundler.py`, `unpacker.py`, `indexer.py`, `clipboard.py` raise `ValueError`, `UnpackError`, `ClipboardError` and return values. Only CLI decides exit code/message. Keeps logic testable with `unittest`. |
| Central format contract in `bundle_format.py` | `serialize()` / `deserialize()` plus tokens (`TITLE_PREFIX`, `SOURCE_PATTERN`, `BINARY_NOTICE`) live in one place. `bundler.py` and `unpacker.py` delegate to it so writer and reader cannot drift. Guarded by round-trip test. |

## Solution Architecture

`bundium` is a local-first, stdlib-only Python CLI. No frontend, no server, no database.

Three flows share one format contract:

```text
pack:   Skill dir -> bundler -> bundle_format.serialize -> clipboard / stdout / .one-page.md
unpack: clipboard / file -> bundle_format.deserialize -> unpacker -> Skill dir
index:  Collection dir -> indexer -> Collection Bundle -> clipboard / stdout / .one-page.md
```

### Component Architecture

| Component | File | Owns |
| :--- | :--- | :--- |
| CLI router | `cli.py` | `argparse` for `pack`, `unpack`, `index`, all `sys.exit` calls, bare-path defaults to `pack` |
| Pack Service | `bundler.py` | File walk, Structure Map tree, delegates assembly to `serialize()` |
| Format contract | `bundle_format.py` | `TITLE_PREFIX`, `SOURCE_PATTERN`, `BINARY_NOTICE`, `serialize()`, `deserialize()`, widening fences |
| Unpack Service | `unpacker.py` | `validate_paths` → `check_collisions` → `write_files`, title sanitizing |
| Index Service | `indexer.py` | `discover_skills()` with `-r` pruning, Skill Index table, Collection Bundle text |
| Frontmatter | `frontmatter.py` | Strict YAML subkeys, `---` vs horizontal-rule handling |
| Clipboard | `clipboard.py` | `pbcopy` / `pbpaste` (macOS), `wl-copy` / `xclip` / `xsel` (Linux), raises `ClipboardError` |
| Shared | `utils.py`, `constants.py` | `is_excluded_path`, language tags, default dir |

Rule: domain modules raise (`UnpackError`, `ValueError`, `ClipboardError`), never exit. Only `cli.py` exits.

### Runtime and Delivery Architecture

| Aspect | Value |
| :--- | :--- |
| Runtime | Local Python 3.9+, no dependencies |
| Install | `uv sync`, run via `uv run bundium`; fallback `pip install -e .` |
| Entry | `bundium` console script, plus `python -m bundium` |
| Delivery Targets | System clipboard (default), terminal stdout (`-t`), file (`-o` → `.one-page.md`) |
| Persistence | Local filesystem only, no network, no secrets |
| Verify | `uv run python -m unittest discover -s tests` |

Deployment details are install instructions in `README.md`, not infrastructure.

## Application Design

### CLI Design

`cli.py` is the only place that talks to the user and the OS exit code. It uses `argparse` with three subcommands.

```bash
bundium pack <skill-dir> [-c | -t | -o] [-f]
bundium unpack [bundle.md] [-c] [-d <dir>] [-f]
bundium index <collection-dir> [-r] [-c | -t | -o] [-f]
bundium <skill-dir>   # bare path still routes to pack
```

| Rule | Detail |
| :--- | :--- |
| Routing | `main()` prepends `pack` when first arg is not `pack`, `unpack`, `index`, `-h`, `-v`. |
| Delivery flags | `-c` clipboard (default), `-t` terminal stdout, `-o` output file. `pack` and `index` make them mutually exclusive. |
| Force | `-f` is the only way to overwrite. `pack` / `index` refuse existing `.one-page.md`, `unpack` refuses existing files in target. |
| Errors | Domain modules raise, `cli.py` converts to `sys.exit("Error: ...")`. No prompts, safe for scripts. |

### Configuration Management

No config files, no environment variables, no secrets.

| Setting | Where | Default |
| :--- | :--- | :--- |
| Package version | `pyproject.toml` + `src/bundium/__init__.py` (`__version__`) | e.g. `0.2.1` |
| Console script | `pyproject.toml` `[project.scripts]` | `bundium = bundium.cli:main`, deprecated alias `skill-bundler` |
| Language tags | `src/bundium/constants.py` (`EXTENSION_LANGUAGE_TAGS`) | Maps file suffix to fence language |
| Excluded paths | `src/bundium/utils.py` (`is_excluded_path`) | Skips `.git`, `__pycache__`, dot-dirs, etc. |
| CLI flags | `src/bundium/cli.py` (`build_parser()`) | `-c` clipboard default, `-t` terminal, `-o` output, `-d` destination, `-f` force, `-r` recursive |

## Presentation Layer (Terminal plus Clipboard)

There is no web UI. The presentation layer is terminal text plus the OS clipboard.

* Help per subcommand via `-h`. Version via `-v`.
* Status lines: `📋 Copied to clipboard (...)`, `✅ Wrote <path>`, `🎉 Successfully unpacked skill to: ...`.
* Output documents are Markdown: Bundle (one Skill in full) and Collection Bundle (Skill Index table + `SKILL.md` bodies).
* Clipboard backend: `pbcopy` / `pbpaste` on macOS, `wl-copy` / `wl-paste`, `xclip`, `xsel` on Linux. Windows raises `ClipboardError`.

Example:

```bash
bundium pack ./my-skill -t
bundium unpack bundle.md -d ./my-skill --force
bundium index ./my-collection -r -t
```

## Service Layer

Pure stdlib logic. No network, no DB. Each service takes paths/text and returns values; `cli.py` handles delivery and exit.

### Pack Service

File: `bundler.py` + `bundle_format.serialize()`.

1. Check `skill_dir` is a dir with top-level `SKILL.md`.
2. `collect_skill_files()` walks files, skips excluded dirs via `is_excluded_path`.
3. `serialize()` builds `**Title:** One Page Version of <title>`, `Source`, Structure Map ASCII tree, `SKILL.md` body, then each Inlined File in widened fences (`max(3, longest backtick run + 1)`), Skipped Files as name + `_binary file — not inlined_`.
4. Return `(document, inlined_count, skipped_files)` for delivery.

### Unpack Service

File: `unpacker.py` + `bundle_format.deserialize()`.

1. Get text from `-c` clipboard (error on empty) or bundle file.
2. `deserialize()` rejects Collection Bundles, requires `<!-- SOURCE: SKILL.md -->`, line-anchored markers + `## <path>` headers + Structure Map cross-check.
3. `extract_skill_title()` sanitizes Title for default `./<skill-title>/` dir, fallback `unpacked-skill` for `.` / `..`.
4. `validate_paths` rejects absolute / `..` escapes, `check_collisions` aborts unless `--force`, `write_files` writes UTF-8.
5. Return `(unpacked_count, skipped_files)`.

### Index Service

File: `indexer.py`.

1. `discover_skills()` finds immediate children with `SKILL.md`. With `-r`, includes nested skills with pruning. Records skipped dirs. Ignores bare `SKILL.md` at collection root to keep output non-unpackable.
2. `build_collection_document()` emits `**Title:** Collection Bundle — <name>`, Skill Index table, then each `SKILL.md` body.
3. Output is deterministic (no timestamp) so it diffs cleanly. Byte size stays small by design — bodies only.

## Bundle Data Model

No database. The data is files plus two Markdown document shapes.

| Shape | Owned by | Contents |
| :--- | :--- | :--- |
| Skill directory | Filesystem | Top-level `SKILL.md` required. Text files → Inlined Files. Binary / undecodable → Skipped Files. |
| Bundle document | `bundle_format.serialize()` | `**Title:** One Page Version of <title>`, `Source`, Structure Map (` ```text ` tree), then per file: `<!-- SOURCE: path -->` + `## path` + fenced content or `_binary file — not inlined_` |
| Collection directory | Filesystem | Immediate children with `SKILL.md` are Skills. Bare root `SKILL.md` ignored. |
| Collection Bundle | `indexer.build_collection_document()` | `**Title:** Collection Bundle — <name>`, Skill Index table, then each `SKILL.md` body. No exact `<!-- SOURCE: SKILL.md -->`, so `unpack` refuses it. |

Invariants: marker on its own line, `## <path>` header right after, fences widen to `max(3, longest backtick run + 1)`.

## Skill Ingestion Architecture

How files enter the system, before any document is built.

```text
walk dir -> is_excluded_path? -> probe binary? -> decode UTF-8? -> inline or skip
```

| Step | How |
| :--- | :--- |
| Walk | `collect_skill_files()` for pack, `discover_skills()` for index. Sorted for determinism. |
| Exclude | `utils.is_excluded_path()` skips `.git`, `__pycache__`, dot-dirs, `*.pyc`, `.DS_Store`. |
| Probe | First 8192 bytes checked for `b"\x00"`. Try UTF-8 decode, else mark Skipped. |
| Frontmatter | `frontmatter.py` parses strict subkeys, preserves `---` rules so `SKILL.md` body survives round-trip. |
| Index pruning | Without `-r`, only immediate children. With `-r`, nested skills included, parent dirs with own `SKILL.md` prune deeper nesting to avoid double-count. |

## Security and Safety Guards

| Control | How |
| :--- | :--- |
| Path traversal guard | `is_safe_relative_path` rejects absolute paths, `..` escapes, and targets resolving to dest root. Checked before any write. |
| Strict validation | Require `SKILL.md` marker, require `## <path>` header after each marker, cross-check against Structure Map, verify fence boundaries. |
| Collision guard | `check_collisions` lists existing files and aborts unless `--force`. Same for `-o` output files. |
| Binary safety | Probe first 8192 bytes for `b"\x00"`, try UTF-8 decode, otherwise emit notice and write nothing. Exact-match check avoids false positives. |
| Clipboard isolation | `clipboard.py` uses `pbcopy` / `pbpaste` (macOS), `wl-copy` / `wl-paste`, `xclip`, `xsel` (Linux) via `subprocess`. Windows raises `ClipboardError`. No shell injection, no secrets stored. |

Safety net: `tests/test_unpacker.py::test_round_trip_pack_and_unpack` must pass after touching `bundler.py` or `unpacker.py`.

## User Journeys Walkthrough

### 1. Pack a Skill to share in an LLM chat

```bash
bundium pack ./my-skill
```

Walkthrough: CLI checks `./my-skill` is a dir with `SKILL.md`. `collect_skill_files` walks files skipping excluded dirs. `serialize` builds Title, Structure Map, `SKILL.md` body, then each Inlined File with widened fences. Default Delivery Target copies to clipboard. User pastes into chat. Variants: `-t` prints, `-o` writes `./my-skill.one-page.md` (refuses overwrite without `--force`).

### 2. Unpack a Bundle back to files

```bash
bundium unpack bundle.md -d ./my-skill
```

Walkthrough: CLI reads file (or `-c` reads clipboard, errors on empty). Derives target dir from `-d` or from Title (sanitized, fallback `unpacked-skill`). `deserialize` rejects Collection Bundles and marker-less input, extracts files + skipped list. `validate_paths` rejects traversal, `check_collisions` aborts on existing files unless `--force`, then `write_files` creates dirs/files UTF-8. Prints extracted + skipped counts.

### 3. Survey a Collection to choose a Skill

```bash
bundium index ./my-collection -r -t
```

Walkthrough: CLI checks collection dir. `discover_skills` finds child (and with `-r`, nested) Skills, records skipped dirs. `build_collection_document` emits Skill Index table then each `SKILL.md` body. Default copies to clipboard, `-t` prints, `-o` writes file. Output is byte-identical across runs (no timestamp) so it diffs cleanly. It is not valid `unpack` input by design — use `pack` to get the chosen Skill in full.
