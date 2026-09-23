# 0002. Architecture and Contract Corrections

**Date**: 2026-09-24  
**Status**: Complete  
**Related**: [ADR 0005](../adr/0005-bundle-delimiter-integrity-and-title-sanitization.md)  

## Summary

This specification consolidates core architectural improvements, contract hardening, and error handling updates across skill bundler. It establishes a single source of truth for bundle markers, prevents marker collision, introduces typed exceptions, and moves structural validations into the domain layer. It also fixes CLI consistency for version flags and overwrite behavior, hardens path traversal security, and establishes comprehensive edge case testing.

## Context

The initial release of skill bundler established the core pack and unpack behavior with backward compatibility. As feature scope expands to whole collection indexing, several contract subtleties and architectural couplings need refinement:

First, bundle markers, fence styles, and binary skip strings are duplicated across bundler and unpacker modules rather than sharing a single constant definition. This leaves room for silent drift when either side changes.

Second, error handling in utility code such as the clipboard module invokes system exit directly instead of raising typed domain exceptions. This limits programmatic reuse by external Python callers and prevents clean testing in headless environments.

Third, frontmatter parsing and marker parsing rely on loose substring checks rather than anchored or exact matching. A file containing markers or extra horizontal rules could cause parsing ambiguities or dropped content.

Fourth, path safety checks in unpacker permit edge cases such as dot only titles or root destination targets. Addressing these issues now ensures a solid, safe, and maintainable foundation before advancing index command development.

## Requirements

**User stories**:
- As a CLI user, I want reliable, safe, and consistent pack, unpack, and index commands that never corrupt data or silently drop files.
- As a developer using skill bundler as a Python library, I want typed exceptions and domain level validation so that I can handle errors gracefully without process termination.
- As a maintainer, I want centralized marker contracts, shared utilities, and independent unit tests so that the codebase is easy to modify without regression risks.

**Acceptance criteria**:

- **AC-1 (Single Source of Truth)**: Bundle markers, title prefixes, binary skip notices, and code fence parameters reside in a dedicated constants module, imported by both bundler and unpacker.
- **AC-2 (Shared Utilities)**: Frontmatter parsing and path exclusion logic live in dedicated shared modules (such as `frontmatter.py` and `utils.py`), removing hidden couplings.
- **AC-3 (No Domain System Exits)**: All domain modules (including clipboard and bundler) raise typed exceptions (`ClipboardError`, `ValueError`, `UnpackError`); `cli.py` remains the only module allowed to invoke `sys.exit`.
- **AC-4 (Explicit Collection Rejection)**: `parse_bundle` raises `UnpackError("Collection Bundles cannot be unpacked.")` immediately when encountering a Collection Bundle header without the single skill marker.
- **AC-5 (Non Destructive Delimiter Parsing and Exact Binary Match)**: Marker parsing anchors to line starts using `(?m)^<!-- SOURCE:\s*(.*?)\s*-->\r?$` supporting both LF and CRLF line endings. The unpacker uses a non destructive sequential parser (`re.finditer`) validated against expected paths extracted from the Structure Map; any marker inside a code block that does not match a declared path is preserved intact within the enclosing file content. Binary file skip checks require exact string equality (`== BINARY_NOTICE`) after stripping whitespace.
- **AC-6 (Strict Frontmatter and Multiline YAML)**: Frontmatter parsing splits only on opening markers, preserves body content containing horizontal rules, and folds multiline description blocks.
- **AC-7 (Hardened Path Safety and Title Sanitization)**: Title extraction sanitizes dot only (`.`), parent (`..`), and hidden directory names (names starting with `.`) by falling back to `DEFAULT_UNPACK_DIR` (`"unpacked-skill"`). Path traversal validation disallows paths resolving directly to the target directory for file entries.
- **AC-8 (CLI Consistency)**: `-v` and `--version` are registered in the argument parser, and `--force` allows `-o` file overwriting across pack and index commands.
- **AC-9 (Efficient I/O and Domain Validation)**: `build_bundle_document` reads `SKILL.md` once, validates structural integrity internally within the domain layer, and eliminates redundant disk reads in `cli.py`.
- **AC-10 (Recursive Discovery Pruning)**: Recursive skill discovery stops traversing deeper once a directory containing `SKILL.md` is found, preventing internal scripts from being counted as skills or skipped folders.
- **AC-11 (Comprehensive Test Suite)**: Unit tests cover all edge cases (extra frontmatter rules, multiline descriptions, marker collisions, path traversal, headless clipboard, and dogfooding on the repository itself).

## Options considered

### Option 1: Modular refactor with shared constants and typed exceptions (Recommended)

Group all format tokens into `constants.py`, extract shared parsing to `frontmatter.py`, convert direct system exits to typed exceptions, and enforce structural assertions in domain functions.

**Pros**:
- Solves all ten identified defect areas cleanly.
- Preserves the zero dependency standard library design.
- Enables library consumers to embed skill bundler safely.

**Cons**:
- Touches multiple files and requires updating test imports.

### Option 2: Incremental inline patches

Fix individual issues (such as version flag and title fallback) directly inside existing modules without introducing new files or centralizing constants.

**Pros**:
- Smaller immediate diff.

**Cons**:
- Leaves hidden couplings between bundler and indexer.
- Duplication between bundler and unpacker markers remains vulnerable to future drift.

## Decision

**Chosen option**: Option 1: Modular refactor with shared constants and typed exceptions.

We will introduce `constants.py` and `frontmatter.py`, convert utility errors to typed exceptions, move validation into domain methods, and extend CLI options with `--force` and `--version`.

## Rationale

Centralizing constants eliminates the risk of string contract drift between the packing and unpacking sides. Raising typed exceptions makes the library embeddable in web services, background workers, or interactive agents without unexpected process exits. Moving validation into the domain layer guarantees data integrity regardless of whether skill bundler is invoked through the CLI or through direct Python imports.

## Standard definition

### Canonical module structure

```
src/skill_bundler/
├── __init__.py         # Public exports and version
├── __main__.py         # CLI invocation entrypoint
├── cli.py              # Argument parsing and sys.exit ownership
├── constants.py        # Centralized markers, fence limits, templates
├── frontmatter.py      # Frontmatter extraction and multiline parsing
├── bundler.py          # Pack logic and domain validation
├── unpacker.py         # Unpack logic and path traversal guards
├── indexer.py          # Collection discovery and indexing
└── clipboard.py        # Clipboard adapter raising ClipboardError
```

### Centralized constants contract

```python
# src/skill_bundler/constants.py
import re

SOURCE_COMMENT_PREFIX = "<!-- SOURCE:"
SOURCE_COMMENT_SUFFIX = "-->"
SOURCE_PATTERN = re.compile(r"(?m)^<!-- SOURCE:\s*(.*?)\s*-->\r?$")

SKILL_MARKER_RELATIVE_PATH = "SKILL.md"
SKILL_MARKER_COMMENT = f"{SOURCE_COMMENT_PREFIX} {SKILL_MARKER_RELATIVE_PATH} {SOURCE_COMMENT_SUFFIX}"

BINARY_NOTICE = "_binary file — not inlined_"
BINARY_PROBE_SIZE = 8192

TITLE_PREFIX = "**Title:** One Page Version of "
COLLECTION_TITLE_PREFIX = "**Title:** Collection Bundle — "

DEFAULT_UNPACK_DIR = "unpacked-skill"
```

### Parser and Backward Compatibility Contracts

- **Structure Map Path Extraction**: `unpacker.py` implements `parse_structure_map_paths(bundle_text: str) -> Set[str]` to extract valid file paths from the preamble.
- **Non Destructive Delimiter Parsing**: `unpacker.parse_bundle` uses `SOURCE_PATTERN.finditer(bundle_text)` to find candidate sections. If a matched path is not present in the Structure Map (or not `SKILL.md`), it is treated as inlined content rather than a file boundary, preventing destructive fragmentation.
- **Backward Compatibility Alias**: `bundler.py` retains `parse_skill = frontmatter.parse_skill` to support existing external scripts importing directly from `skill_bundler.bundler`.

## Build plan

1. Create `src/skill_bundler/constants.py` with constants and `SOURCE_PATTERN`, satisfies **AC-1**
2. Create `src/skill_bundler/frontmatter.py` with strict splitting and multiline description folding, satisfies **AC-2**, **AC-6**
3. Refactor `src/skill_bundler/clipboard.py` to raise `ClipboardError` instead of calling `sys.exit`, satisfies **AC-3**
4. Update `src/skill_bundler/bundler.py` to read `SKILL.md` once, maintain `parse_skill` alias, validate structural integrity internally, and return emitted paths, satisfies **AC-2**, **AC-5**, **AC-9**
5. Update `src/skill_bundler/unpacker.py` with Structure Map path extraction, non destructive sequential marker parsing (`re.finditer` with CRLF support), exact binary notice matching, explicit Collection Bundle rejection, and hardened title/path checks, satisfies **AC-4**, **AC-5**, **AC-7**
6. Refactor `src/skill_bundler/cli.py` to handle `ClipboardError`, register `-v` / `--version`, accept `--force` for `-o` overwrite across subcommands, and remove duplicate file reads, satisfies **AC-3**, **AC-8**, **AC-9**
7. Implement `src/skill_bundler/indexer.py` with pruned recursive search to prevent nested script directory leakage, satisfies **AC-10**
8. Expand test suite in `tests/` with edge case tests for frontmatter, traversal, clipboard fallbacks, marker contracts, and dogfooding, satisfies **AC-11**
9. Update `AGENTS.md` and `src/skill_bundler/AGENTS.md` with the new module layout and dependency relationships, satisfies **AC-1**, **AC-2**

## Consequences

**Positive**:
- Single source of truth prevents formatting drift.
- Eliminates risk of process exit when skill bundler is used as a library.
- Stronger path safety protects against malicious bundle structures.
- Faster execution by eliminating duplicate disk I/O.
- Full parity between CLI options across all subcommands.

**Negative / tradeoffs**:
- Introduces two new internal modules (`constants.py`, `frontmatter.py`).
- Existing code importing private helpers may need updated imports (mitigated by retaining public aliases in `__init__.py`).

**Neutral**:
- Zero external runtime dependencies preserved.
- Python 3.9+ compatibility remains standard.

## Follow-up

- [x] Implement build tasks 1 through 5 (core domain hardening).
- [x] Implement build tasks 6 and 7 (CLI updates and indexer pruning).
- [x] Implement build tasks 8 and 9 (comprehensive test suite and documentation sync).

## References

**Project sources**:
- `AGENTS.md`: standard library and CLI error handling rules
- `CONTEXT.md`: canonical vocabulary for Bundle, Collection, and Structure Map
- `docs/adr/0001-subcommand-cli-architecture.md`: CLI structure
- `docs/adr/0002-safe-overwrite-guard-on-unpack.md`: overwrite protection
- `docs/adr/0003-strict-bundle-validation-and-safety.md`: path safety
- `docs/adr/0004-collection-bundle-contract.md`: Collection Bundle format contract
- `docs/adr/0005-bundle-delimiter-integrity-and-title-sanitization.md`: delimiter integrity and title sanitization
