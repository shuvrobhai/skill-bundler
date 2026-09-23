# 0001 — `index`: bundle a whole Collection into one Markdown document

Status: proposed, awaiting review
Related: [ADR 0004](../adr/0004-collection-bundle-contract.md)

## Problem

`pack` bundles exactly one Skill: it requires `SKILL.md` at the top of the directory it is pointed
at. Pointing it at a Collection therefore fails outright.

```
$ skill-bundler pack .workbuddy-ai/skills -t
Error: '.../skills/SKILL.md' does not exist (SKILL.md is required).
exit code: 1
```

There is no way to hand an LLM a single document that says "here are the Skills I have".

## What this builds

A third subcommand, `index`, that reads a Collection and emits one **Collection Bundle**: a Skill
Index listing every Skill, followed by one section per Skill holding its `SKILL.md` body.

## CLI surface

```
skill-bundler index <collection-dir> [-r|--recursive] [-c|--clipboard] [-t|--terminal] [-o|--output]
```

The Delivery Target flags mirror `pack` exactly and stay mutually exclusive: clipboard by default,
`-t` for stdout, `-o` for a file.

`index` must also be added to the subcommand whitelist in `cli.py` `main()`. Without that the
backward-compatibility shim rewrites `skill-bundler index .` into `pack index .` and the new
command is unreachable.

## Discovery rules

A **Skill** here is a directory that directly contains a `SKILL.md`.

- Default: only the immediate children of `<collection-dir>`, i.e. the equivalent of
  `<collection-dir>/*/SKILL.md`.
- `-r` / `--recursive`: search the whole tree beneath `<collection-dir>`, so nested Skills are
  found too. Without the flag they are silently invisible, which is the only reason it exists.
- Entries starting with `.` and any `__pycache__` directory are skipped at every level. The
  `<collection-dir>` itself may be hidden — `.workbuddy-ai/skills` is a normal target.
- A directory without a `SKILL.md` is not a Skill: it is skipped, counted, and reported in the
  summary line.
- **A `SKILL.md` sitting directly in `<collection-dir>` is never included.** Only Skills beneath it
  are. This is what keeps the literal string `<!-- SOURCE: SKILL.md -->` out of a Collection
  Bundle, which is the whole reason `unpack` cannot read one. See ADR 0004.
- Zero Skills found is an error: message, exit code 1, nothing written.

## Document format

```
**Title:** Collection Bundle — <collection dir name>
**Source:** [<uri>](<uri>)
**Skills:** <count>

---

# Skill Index

| Skill | Description | Path |
|---|---|---|
| architect | Run /architect when choosing between approaches, designing a feature or page… | architect/SKILL.md |

---

<!-- SOURCE: architect/SKILL.md -->

## architect

<SKILL.md body>

---

<!-- SOURCE: audit/SKILL.md -->

## audit

<SKILL.md body>
```

Rules:

- The header deliberately does **not** reuse `**Title:** One Page Version of ...`, so a Collection
  Bundle can never be mistaken for a single-Skill Bundle.
- No generation timestamp. The same Collection must produce a byte-identical document on every
  run, so the output can be diffed and committed.
- **Skill Index** columns are `name | description | path`, one row per Skill, sorted by Skill name,
  case-insensitively.
- `name` comes from the `SKILL.md` frontmatter `name:` field, falling back to the directory name
  when there is no frontmatter.
- `description` comes from the frontmatter `description:` field, with newlines collapsed to
  spaces, `|` escaped as `\|`, and the result truncated to 80 characters with `…` appended.
- Section heading is `## <name>`, matching the index row. The path already appears in the index
  and in the `<!-- SOURCE: -->` comment, so it is not repeated a third time.
- No Structure Map. The Skill Index already names every Skill and its path, so a tree of the whole
  Collection would be long and would say nothing new.

## Delivery

| Flag | Behaviour |
|---|---|
| none, or `-c` | Copy the Collection Bundle to the System Clipboard |
| `-t` / `--terminal` | Print to stdout |
| `-o` / `--output` | Write `<collection-dir>.one-page.md` next to the Collection |

`-o` refuses to overwrite an existing file, exactly as `pack` does. `.gitignore` already covers
`*.one-page.md`.

Summary line:

```
✅ 19 skills indexed, 2 folders skipped → .workbuddy-ai/skills.one-page.md
```

## Out of scope

- **`unpack` does not read a Collection Bundle.** It already rejects one, because the
  `<!-- SOURCE: SKILL.md -->` marker is absent. Reconstructing a Collection from a single bundle
  is a separate feature. See ADR 0004.
- **Supporting files are never inlined, only `SKILL.md`.** Inlining everything in
  `.workbuddy-ai/skills` would be 713,487 bytes across 106 files (~178k tokens); the 19 `SKILL.md`
  files alone are already 185,893 bytes (~46k tokens). Use `pack` on the one Skill that is
  actually wanted. See ADR 0004.
- **Content inside a `SKILL.md` is not escaped.** A body containing a line shaped like
  `<!-- SOURCE: x -->` would add a spurious marker. Nothing parses a Collection Bundle back, so
  this is harmless today.
- An `--index-only` mode that omits the bodies.

## Module layout

New module `src/skill_bundler/indexer.py`, mirroring the `bundler.py` / `unpacker.py` split.

| Function | Job |
|---|---|
| `discover_skills(collection_dir, recursive)` | Return `(skills, skipped_dir_names)` |
| `build_collection_document(collection_dir, skills)` | Return the Collection Bundle text |
| `_truncate(text, limit)` | Private. Collapse whitespace, cut to `limit`, append `…` |
| `_table_cell(text)` | Private. Escape `|` for a Markdown table cell |

`SkillEntry` is a `NamedTuple` of `name`, `description`, `relative_path`, `skill_md`. `cli.py`
gains `_handle_index` and stays the only place that calls `sys.exit`. Public names are re-exported
through `__all__` in `__init__.py`.

## Acceptance criteria

`tests/test_indexer.py`, `unittest.TestCase`, one test per rule:

1. Three Skills in a temp Collection produce a document with three index rows and three sections.
2. Skills are in case-insensitive alphabetical order, and index order matches section order.
3. A directory with no `SKILL.md` is skipped and counted in the summary.
4. A Collection with no Skills raises, and no file is written.
5. A `SKILL.md` directly in the Collection directory is ignored, and the document never contains
   the literal `<!-- SOURCE: SKILL.md -->`.
6. A description over 80 characters is truncated with `…`; a description containing `|` is escaped.
7. A Skill with no frontmatter falls back to its directory name.
8. Default mode finds no nested Skill; `--recursive` finds it.
9. Hidden directories and `__pycache__` are skipped.
10. `-o` writes `<collection-dir>.one-page.md` and refuses to overwrite an existing file.

## Docs to update when this ships

- `README.md`: the `index` command, its flags, and the Collection Bundle.
- `src/skill_bundler/AGENTS.md`: add `indexer.py` to the key files table, and note that a
  Collection Bundle is not a valid `unpack` input.
- `AGENTS.md`: the `## Commands` block.
