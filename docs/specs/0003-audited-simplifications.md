# 0003. Audited Simplifications and Over-Engineering Remediation

**Date**: 2026-10-18  
**Status**: In-Progress  
**Related**: [ADR 0005](../adr/0005-bundle-delimiter-integrity-and-title-sanitization.md), [ADR 0006](../adr/0006-delimiter-anchoring-without-structure-map.md)  

## Summary

This specification defines the implementation requirements for executing the ponytail audit cuts. It eliminates over-engineering, consolidates fragmented modules, removes brittle ASCII tree parsing, drops obsolete compatibility shims, and leverages native standard library capabilities.

## Context

Following the initial releases and contract hardening (specs 0001 and 0002), a repository-wide audit revealed several areas of over-engineering:
1. `bundle_format.py` contains 32 lines of ASCII tree reverse-parsing to cross-check file section headers against indentation depth in the Structure Map preamble. Delimiters are already line-anchored and paired with section headers; reverse-parsing ASCII trees adds fragility with zero safety benefits.
2. `constants.py` was reduced in previous refactors to just two constants (`EXTENSION_LANGUAGE_TAGS` and `DEFAULT_UNPACK_DIR`), separating them unnecessarily from the core format constants in `bundle_format.py`.
3. `utils.py` contains an 11-line module defining `is_excluded_path`, which is dead/redundant in `bundler.py` (where `os.walk` already prunes hidden files and directories) and is a simple one-line check in `indexer.py`.
4. `is_safe_relative_path` in `unpacker.py` manually iterates over `dest.parents` to detect directory escape instead of using Python 3.9's native `Path.is_relative_to`.
5. `cli.py` duplicates the mutually exclusive delivery group (`-c`, `-t`, `-o`, `-f`) between `pack` and `index`.
6. Obsolete compatibility shims persist: `directory_tree` in `bundler.py` and `__init__.py`, `force` as an alias for `should_overwrite` in `unpack_bundle`, and `skill-bundler` in `pyproject.toml`.

## Requirements

**Acceptance criteria**:

- **AC-1 (Parser Simplification / ADR-0006)**: `parse_structure_map_paths` is removed from `bundle_format.py`. `deserialize` determines valid file sections strictly by matching `(?m)^<!-- SOURCE:\s*(.*?)\s*-->$` followed immediately by `## <path>`, without reading or parsing the Structure Map preamble.
- **AC-2 (Constants Consolidation)**: `EXTENSION_LANGUAGE_TAGS` and `DEFAULT_UNPACK_DIR` are moved into `bundle_format.py`. `src/bundium/constants.py` is removed.
- **AC-3 (Utils Elimination)**: `src/bundium/utils.py` is removed. `bundler.py` drops redundant path exclusion calls; `indexer.py` checks `child.name.startswith(".") or child.name == "__pycache__"` directly.
- **AC-4 (Stdlib Relative Path Check)**: `is_safe_relative_path` in `unpacker.py` uses `dest.is_relative_to(target_resolved) and dest != target_resolved`.
- **AC-5 (CLI Flag Deduplication)**: CLI delivery options (`-c`, `-t`, `-o`, `-f`) are configured via a shared helper function in `cli.py`.
- **AC-6 (Removal of Dead Shims)**:
  - `directory_tree` is removed from `bundler.py` and `__init__.__all__`.
  - `force` argument is removed from `unpack_bundle` in `unpacker.py`.
  - `skill-bundler = "bundium.cli:main"` is removed from `pyproject.toml`.
- **AC-7 (Hook Configuration Fix)**: `.agents/hooks.json` references `./hooks/*.sh` or valid working-directory-relative paths.
- **AC-8 (Test Suite Health)**: All unit tests in `tests/` pass with zero regressions.
