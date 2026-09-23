# skill-bundler

## Stack

- **Language / Runtime**: Python 3.9+, standard library only, zero runtime dependencies
- **Framework**: none. `argparse` subcommand CLI
- **Key dependencies**: none to run; `setuptools >= 61` to build
- **Package manager**: pip, `src/` layout, installed editable

## Build approach

<TBD, set by /scope>

## Commands

```bash
# Install (editable, provides the skill-bundler command)
pip install -e .

# Run
skill-bundler pack <skill-dir>          # clipboard by default, -o writes a file
skill-bundler unpack <bundle.md> -d <dir>

# Test (install first, or prefix with PYTHONPATH=src)
python -m unittest discover -s tests
```

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
- Domain modules raise `UnpackError` and return values; `cli.py` is the only place that calls `sys.exit`.
- Do not list, track, or document installed agent skills or skill directories in AGENTS.md, README.md, or any context file. Never add an Agent skills section unless explicitly requested by the user (see `.agents/rules/skills-policy.md`).

## Context files

- [src/skill_bundler/AGENTS.md](src/skill_bundler/AGENTS.md): package internals and the bundle format contract
- [.agents/rules/naming-style.md](.agents/rules/naming-style.md): code naming conventions and domain vocabulary guidelines
- [.agents/rules/skills-policy.md](.agents/rules/skills-policy.md): skills documentation restrictions

_Drafted by /audit from the repo, worth a quick human pass. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
