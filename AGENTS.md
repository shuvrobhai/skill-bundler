# Bundium

## Stack

- **Language / Runtime**: Python 3.9+, standard library only, zero runtime dependencies
- **Framework**: none. `argparse` subcommand CLI
- **Key dependencies**: none to run; `setuptools >= 61` to build
- **Package manager**: uv (`uv sync`, `uv run`), `src/` layout; fallback `pip install -e .`

## Build approach

Tracer Bullet (each feature end to end through CLI plus logic, working).

## Commands

```bash
# Install once (editable env, provides the bundium command)
uv sync
# Fallback without uv:
pip install -e .

# Also works without install:
uv run python -m bundium pack /path/to/skill

# Pack: bare path defaults to pack (backward compat); -c/-t/-o are mutually exclusive
bundium pack <skill-dir>                  # clipboard (default)
bundium pack <skill-dir> -t               # stdout
bundium pack <skill-dir> -o [--force]     # writes <skill>.one-page.md next to skill dir; refuses to overwrite unless --force
bundium <skill-dir>                       # bare path also defaults to pack

# Unpack: needs a source; destination defaults to ./<skill-title>/
bundium unpack <bundle.md> -d <dir>            # from file
bundium unpack -c -d <dir>                     # from clipboard
bundium unpack <bundle.md> -d <dir> --force    # only way to overwrite

# Index: survey a whole Collection (Delivery Target flags mirror pack)
bundium index <collection-dir> -t              # stdout (clipboard is default, -o writes file)
bundium index <collection-dir> -r -t           # include nested skills
bundium index <collection-dir> -o [--force]    # writes <collection>.one-page.md; refuses to overwrite unless --force

# Test (uv sync first; use uv run on macOS)
uv run python -m unittest discover -s tests
uv run python -m unittest tests.test_bundler -v        # one module
uv run python -m unittest tests.test_unpacker.TestUnpacker.<test> -v  # one test
```

## Notes

- Clipboard: macOS built in (`pbcopy`/`pbpaste`); Linux needs `wl-copy`/`wl-paste`, `xclip`, or `xsel`; Windows unsupported.
- Round-trip safety net: `tests/test_unpacker.py::test_round_trip_pack_and_unpack` guards the pack/unpack format contract — run it after touching `bundler.py` or `unpacker.py`.

## Specs and decisions

Three files hold the project's written record. Each has one job; keep them apart.

| File | Holds | Editable? |
|---|---|---|
| `CONTEXT.md` | The glossary: what the domain words mean, and the words to avoid. No implementation detail, no process rules. | Yes, whenever a term changes. |
| `docs/specs/NNNN-title.md` | What to build and how, for one feature. Written before the code, and the code follows it. | Yes, freely, until the code is written. |
| `docs/adr/NNNN-slug.md` | Why one durable decision was made. | No. A changed mind gets a new ADR, plus `superseded by ADR-NNNN` on the old one. |

A spec names the ADRs it depends on. An ADR is a short paragraph: the context, the decision, and
why. Add `Considered Options` or `Consequences` only when they earn their place. A decision earns
an ADR only if it is hard to reverse, surprising without context, and the result of a real
trade-off; otherwise it is just a spec detail. ADRs 0001 to 0003 predate this and use a longer
Context / Decision / Consequences shape, left as they are.

Numbering is sequential per directory: check the highest existing file and add one.

## Rules

- Standard library only. Do not add a third party runtime dependency.
- Keep `unittest` as the test runner. Tests are `unittest.TestCase` classes in `tests/`.
- Use the domain words from `CONTEXT.md` (Skill, Bundle, Structure Map, Inlined File, Skipped File, Delivery Target) and avoid the alternatives it lists.
- Naming: `snake_case` for functions and variables, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants, `_` prefix for private helpers, booleans start with `is_`, `has_`, `can_`, or `should_`. Detailed rules live in `.agents/rules/naming-style.md`.
- Build the minimum that works. No unrequested abstractions or dependencies, delete rather than add.
- Domain modules raise `UnpackError`, `ValueError`, or `ClipboardError` and return values; `cli.py` is the only place that calls `sys.exit`.
- Do not list, track, or document installed agent skills or skill directories in AGENTS.md, README.md, or any context file. Never add an Agent skills section unless explicitly requested by the user (see `.agents/rules/skills-policy.md`).

## Context files

- [src/bundium/AGENTS.md](src/bundium/AGENTS.md): package internals and the bundle format contract
- [.agents/rules/naming-style.md](.agents/rules/naming-style.md): code naming conventions and domain vocabulary guidelines
- [.agents/rules/skills-policy.md](.agents/rules/skills-policy.md): skills documentation restrictions
- [.agents/rules/ponytail.md](.agents/rules/ponytail.md): minimal-diff, stdlib-first implementation style
- [src/bundium/constants.py](src/bundium/constants.py): centralized format tokens, markers, and probe sizes used by bundler and unpacker
- [src/bundium/frontmatter.py](src/bundium/frontmatter.py): strict YAML frontmatter parsing and horizontal rule preservation
