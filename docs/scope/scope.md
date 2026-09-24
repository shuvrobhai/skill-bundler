# Scope: skill-bundler

A stdlib only CLI that packs an AI agent Skill into one shareable Bundle, unpacks it back, and surveys a whole Collection. Built for anyone passing skills into LLM sessions.

**Build approach:** Tracer Bullet (each feature end to end through CLI plus logic, working).
**Workflow:** Beta (check verify, then test). The project default level of rigor. `/architect` is the recommended first stop for a feature with a real decision, but skippable when you already know the build. Any feature can carry its own tag (e.g. `· GA`) to do more or less.

_These are recommendations to keep your build orderly, not requirements. Skip anything that does not fit: if you already know how to build a feature, use `/develop` and skip `/architect`. You decide when a feature is `done`._

## At a glance

| # | Feature | Phase | Status |
|---|---------|-------|--------|
| A | Pack a skill | Shipped | existing |
| B | Unpack a bundle | Shipped | existing |
| C | Index a collection survey | Shipped | done |
| D | Architecture and contract corrections | Shipped | done |
| E | Release 0.2.0 closeout | Next | planned |
| F | Contract hardening and parser fixes | Next | planned |

## Shipped

### A. Pack a skill · existing
Bundle one Skill directory into a single Markdown document: metadata, Structure Map, every Inlined File, names of Skipped Files, delivered to the clipboard, stdout, or a `.one-page.md` file. code in `src/skill_bundler/bundler.py`, `src/skill_bundler/cli.py`

### B. Unpack a bundle · existing
Rebuild a Skill directory from a Bundle, from a file or the clipboard, with strict validation, path traversal guards, and a refuse to overwrite guard unless `--force` is passed. code in `src/skill_bundler/unpacker.py`, `src/skill_bundler/cli.py`

### C. Index a collection survey · done
Survey a whole Collection into one Collection Bundle: a Skill Index table plus each `SKILL.md` body, immediate children by default, nested skills with `-r`. Only `SKILL.md` files ride along; a survey is never valid `unpack` input.
**Done when:** spec 0001 reads Accepted and the feature is marked done.
- [x] Build it: `/develop index` (spec 0001, code in `src/skill_bundler/indexer.py`, 10 tests green, verified live against 19 real skills)
- [x] Close it: flip spec 0001 to Accepted and mark done
Spec 0001 · code in `src/skill_bundler/indexer.py`

### D. Architecture and contract corrections · done
Consolidate bundle markers in `constants.py`, extract `frontmatter.py`, raise typed `ClipboardError`, anchor delimiters to line starts, enforce exact binary notices, sanitize dot only titles, and add comprehensive edge case tests.
**Done when:** spec 0002 acceptance criteria met, all vulnerability tests pass, and domain modules are free of `sys.exit`.
- [x] Design it (spec): `/architect` (done, spec 0002)
- [x] Build it: `/develop 0002` (constants, frontmatter, clipboard, bundler, unpacker, cli)
- [x] Verify it: `/check verify 0002` (46 tests green, manual checks passed)
- [x] Test it: `/test 0002` (comprehensive test suite including frontmatter, cli, clipboard, dogfood)
Spec 0002 · code in `src/skill_bundler/`

## Next

### E. Release 0.2.0 closeout
Ship what is built: commit the release notes and changelog, tag `v0.2.0`, close all specs, and verify `skill-bundler --version`.
**Done when:** docs committed, `v0.2.0` tagged, spec 0002 Accepted, and `--version` exits 0.
- [ ] Commit and tag: release notes plus changelog in, `v0.2.0` tag pushed
- [x] Settle `--version`: wire `action="version"` in `build_parser()`
- [ ] Optional review: `/check review` before the tag if you want the gate

## Deferred
Out of scope for the current build pass, kept so the plan stays honest.
- **Collection unpack round trip**: rebuild a Collection from a Collection Bundle · needs a decision (ADR 0004 ruled it a separate feature)
- **`--index-only` mode**: survey with the Skill Index and no bodies · needs a decision (spec 0001 left it out of scope)

## Legend

- **Next step** = the first unticked box (always a command or a tracked milestone).
- **Status** `planned` → `in-progress` → `done`, plus `existing` (built before this scope, left alone by `/develop` and `/sync`) .
- **Pointer line** (`spec <n> · code in <path>`) appears only once those exist.
- **Atomic build tasks live in the spec, not here.** This file carries intent, the `Done when` line, and boxes only.
