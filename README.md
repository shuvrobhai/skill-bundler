# Bundium

Bundle a folder of Markdown files — e.g. an AI agent skill — into a single, self-contained document, or unpack a bundle back into a ready-to-use directory.

By default, bundling copies Markdown to your clipboard ready to paste into any chat or LLM context.

## Repo Metadata

- Author: [shuvrobhai]
- Repository: [https://github.com/shuvrobhai/bundium]

## Table of Contents

- [Key Project Documentation](#key-project-documentation)
- [Key Links](#key-links)
- [Project Structure](#project-structure)
- [Architecture and Tech Stack - at a Glance](#architecture-and-tech-stack---at-a-glance)
- [Quick Start: Working With This Repo](#quick-start-working-with-this-repo)
- [Usage](#usage)
- [Flags Reference](#flags-reference)
- [Security & Safety Guardrails](#security--safety-guardrails)
- [Useful Commands](#useful-commands)

## Key Project Documentation

| Document | Description |
| --- | --- |
| [README.md](README.md) | This file — the developer front door |
| [docs/scope/scope.md](docs/scope/scope.md) | Project roadmap: shipped features, next, and deferred |
| [docs/specs/0000-bundium.md](docs/specs/0000-bundium.md) | The whole tool on one page: CLI surface, document contracts, conventions |
| [docs/specs/0001-index-command.md](docs/specs/0001-index-command.md) | The `index` subcommand: discovery rules, document format, acceptance criteria |
| [docs/architecture-and-walkthrough.md](docs/architecture-and-walkthrough.md) | Architecture, design decisions, bundle formats, user journeys |
| [docs/testing.md](docs/testing.md) | Testing tooling, categories, and commands |
| [deployment/README.md](deployment/README.md) | Release and distribution guidance |
| [CONTEXT.md](CONTEXT.md) | Domain glossary and ubiquitous language |
| [AGENTS.md](AGENTS.md) | Guidance for AI coding agents |
| [CLAUDE.md](CLAUDE.md) | Claude Code entry point (imports `AGENTS.md`) |

## Key Links

- [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
- [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
- [uv package manager](https://docs.astral.sh/uv/)

## Project Structure

```text
bundium/
├── CONTEXT.md                     # Domain glossary & ubiquitous language
├── README.md                      # This file
├── AGENTS.md                      # AI agent guidance
├── CLAUDE.md                      # Claude Code entry point
├── pyproject.toml                 # Package config & console script entrypoint
├── CHANGELOG.md                   # Keep a Changelog format
├── docs/
│   ├── architecture-and-walkthrough.md   # Architecture, design decisions, journeys
│   ├── testing.md                 # Testing & quality assurance
│   ├── scope/
│   │   └── scope.md               # Project roadmap
│   └── specs/
│       ├── 0000-bundium.md        # Whole tool spec
│       └── 0001-index-command.md  # Index subcommand spec
├── deployment/
│   └── README.md                  # Release & distribution
├── src/
│   └── bundium/                   # Core Python package
│       ├── __init__.py            # Public exports and version
│       ├── __main__.py            # python -m bundium entrypoint
│       ├── cli.py                 # Subcommand CLI parser & dispatcher
│       ├── constants.py           # Centralized format tokens and markers
│       ├── bundle_format.py       # Bundle serialization & deserialization
│       ├── frontmatter.py         # Strict YAML frontmatter parsing
│       ├── bundler.py             # Pack logic
│       ├── unpacker.py            # Unpack logic
│       ├── indexer.py             # Index (collection survey) logic
│       ├── utils.py               # Shared path exclusion predicate
│       └── clipboard.py           # OS clipboard adapter
└── tests/                         # Automated test suite
    ├── test_bundler.py
    ├── test_unpacker.py
    └── test_indexer.py
```

## Architecture and Tech Stack - at a Glance

Bundium is a **stdlib-only Python CLI** with **zero runtime dependencies**. It targets **Python 3.9+**, uses the **`src/` layout**, and installs via **`uv sync`**. The CLI is built on **`argparse`** with three subcommands: `pack`, `unpack`, and `index`.

The keystone of the codebase is the **bundle format contract** — a single Markdown document that both `bundle_format.serialize` (writer) and `bundle_format.deserialize` (reader) must agree on, guarded by a round-trip test.

See [docs/architecture-and-walkthrough.md](docs/architecture-and-walkthrough.md) for details.

## Quick Start: Working With This Repo

### Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) (recommended) or `pip`
- A system clipboard utility:
  - macOS: `pbcopy` / `pbpaste` (built in)
  - Linux: `wl-copy`/`wl-paste`, `xclip`, or `xsel`
  - Windows: unsupported

### One-Time Setup

```bash
uv sync
```

Fallback without `uv`:

```bash
pip install -e .
```

### Per Dev Session

```bash
# Run the CLI without installing:
uv run python -m bundium pack /path/to/skill

# Or installed:
uv run bundium pack /path/to/skill
```

## Usage

### 1. Bundling a Skill (`pack`)

```bash
# Copy to clipboard (default)
bundium /path/to/skill
bundium pack /path/to/skill

# Print to terminal (stdout)
bundium pack /path/to/skill -t

# Save as <skill>.one-page.md next to the skill directory
bundium pack /path/to/skill -o
```

### 2. Unpacking a Skill (`unpack`)

```bash
# Unpack directly from clipboard into ./<skill-title>/
bundium unpack -c

# Unpack from clipboard into a specific folder
bundium unpack -c -d ~/.config/skills/my-skill

# Unpack from a Markdown file
bundium unpack path/to/bundle.md -d ./my-skill

# Overwrite existing files in destination
bundium unpack path/to/bundle.md -d ./my-skill --force
```

### 3. Surveying a Collection (`index`)

```bash
# Copy the survey to clipboard (default)
bundium index /path/to/collection

# Print to terminal (stdout)
bundium index /path/to/collection -t

# Save as <collection>.one-page.md next to the collection
bundium index /path/to/collection -o

# Include skills nested below immediate children
bundium index /path/to/collection -r -t
```

Point `index` at a folder of skills to get one survey document. It lists every skill in a table, then includes each `SKILL.md` body in full. Only `SKILL.md` files are included, so use `pack` when you want one skill with all of its supporting files. A survey document is not a valid `unpack` input.

## Flags Reference

### `pack` Flags

| Flag | Description |
| --- | --- |
| `-c`, `--clipboard` | Copy bundle to clipboard (default) |
| `-t`, `--terminal` | Print bundle to terminal (`stdout`) |
| `-o`, `--output` | Write `<skill>.one-page.md` file next to skill directory |

### `unpack` Flags

| Flag | Description |
| --- | --- |
| `-c`, `--clipboard` | Read bundle directly from system clipboard |
| `-d`, `--destination` | Target directory for unpacked skill (defaults to `./<skill-title>/`) |
| `-f`, `--force` | Overwrite existing files in destination directory |

### `index` Flags

| Flag | Description |
| --- | --- |
| `-r`, `--recursive` | Include skills nested below immediate children |
| `-c`, `--clipboard` | Copy survey to clipboard (default) |
| `-t`, `--terminal` | Print survey to terminal (`stdout`) |
| `-o`, `--output` | Write `<collection>.one-page.md` file next to collection |

## Security & Safety Guardrails

- **Path Traversal Protection**: Rejects bundles attempting to write files outside the target directory (e.g. `../` relative path attacks).
- **Collision Guard**: Prevents accidental overwriting of local files unless `--force` / `-f` is explicitly provided.
- **Strict Bundle Validation**: Validates that `SKILL.md` and complete code fences are present before writing to disk.

## Useful Commands

| Command | Purpose |
| --- | --- |
| `uv sync` | Install the project into an editable environment |
| `uv run python -m unittest discover -s tests` | Run the full test suite |
| `uv run python -m unittest tests.test_bundler -v` | Run one test module |
| `uv run python -m unittest tests.test_unpacker.TestUnpacker.<test> -v` | Run one test |
| `uv run bundium pack <dir>` | Pack a skill |
| `uv run bundium unpack <file>` | Unpack a bundle |
| `uv run bundium index <dir>` | Survey a collection |