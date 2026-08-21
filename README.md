# Skill Bundler

Bundle an AI agent skill directory into a single, self-contained Markdown file, or unpack a bundle back into a ready-to-use skill directory.

By default, bundling copies Markdown to your clipboard ready to paste into any chat or LLM context.

## Requirements

- Python 3.9+ with standard library only
- Clipboard utility:
  - macOS uses `pbcopy` / `pbpaste` (built in)
  - Linux uses `wl-copy`/`wl-paste`, `xclip`, or `xsel`
  - Windows clipboard is not supported

## Installation

Install in editable mode for the CLI command:

```bash
pip install -e .
```

## Usage

### 1. Bundling a Skill (`pack`)

```bash
# Copy to clipboard (default)
skill-bundler /path/to/skill
# or explicitly:
skill-bundler pack /path/to/skill

# Print to terminal (stdout)
skill-bundler pack /path/to/skill -t

# Save as <skill>.one-page.md next to the skill directory
skill-bundler pack /path/to/skill -o
```

### 2. Unpacking a Skill (`unpack`)

```bash
# Unpack directly from clipboard into ./<skill-title>/
skill-bundler unpack -c

# Unpack from clipboard into a specific folder
skill-bundler unpack -c -d ~/.gemini/config/skills/my-skill

# Unpack from a Markdown file
skill-bundler unpack path/to/bundle.md -d ./my-skill

# Overwrite existing files in destination
skill-bundler unpack path/to/bundle.md -d ./my-skill --force
```

## Flags Reference

### `pack` Flags

| Flag | Description |
|------|-------------|
| `-c`, `--clipboard` | Copy bundle to clipboard (default) |
| `-t`, `--terminal` | Print bundle to terminal (`stdout`) |
| `-o`, `--output` | Write `<skill>.one-page.md` file next to skill directory |

### `unpack` Flags

| Flag | Description |
|------|-------------|
| `-c`, `--clipboard` | Read bundle directly from system clipboard |
| `-d`, `--destination` | Target directory for unpacked skill (defaults to `./<skill-title>/`) |
| `-f`, `--force` | Overwrite existing files in destination directory |

## Project Structure

```
skill-bundler/
├── CONTEXT.md                    # Domain glossary & ubiquitous language
├── README.md                     # Documentation & CLI reference
├── pyproject.toml                # Package configuration & console script entrypoint
├── docs/
│   └── adr/                      # Architectural Decision Records (ADRs 0001, 0002, 0003)
├── src/
│   └── skill_bundler/            # Core Python package
│       ├── __init__.py
│       ├── __main__.py          # python -m skill_bundler entrypoint
│       ├── bundler.py           # Pack logic (parser, tree, code inliner)
│       ├── unpacker.py          # Unpack logic (parser, path security, disk writer)
│       ├── cli.py               # Subcommand CLI parser & dispatcher
│       └── clipboard.py         # OS clipboard adapter (pbcopy/pbpaste, wl-copy/paste, xclip)
└── tests/                        # Automated test suite
    ├── test_bundler.py           # Unit tests for bundling & filtering
    └── test_unpacker.py          # Unit tests for round-trip unpacking & security guards
```

## Security & Safety Guardrails

- **Path Traversal Protection**: Rejects bundles attempting to write files outside the target directory (e.g. `../` relative path attacks).
- **Collision Guard**: Prevents accidental overwriting of local files unless `--force` / `-f` is explicitly provided.
- **Strict Bundle Validation**: Validates that `SKILL.md` and complete code fences are present before writing to disk.