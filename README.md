# Skill Bundler

Bundle an AI agent skill directory into a single, self-contained Markdown file.

By default, the generated Markdown is copied to your clipboard ready to paste into any chat or LLM context.

## Requirements

- Python 3.9+ with standard library only
- Clipboard utility:
  - macOS uses `pbcopy` (built in)
  - Linux uses `wl-copy`, `xclip`, or `xsel`
  - Windows clipboard is not supported

## Installation

Install in editable mode for the CLI command:

```bash
pip install -e .
```

## Usage

You can run `skill-bundler` in three ways:

```bash
# 1. As installed CLI command:
skill-bundler /path/to/skill

# 2. As Python module:
python3 -m skill_bundler /path/to/skill

# 3. As standalone script:
python3 skill_bundler.py /path/to/skill
```

### Flags (Delivery Targets)

| Flag | Description |
|------|-------------|
| `-c`, `--clipboard` | Copy to clipboard (default) |
| `-t`, `--terminal` | Print to terminal (`stdout`) |
| `-o`, `--output` | Write `<skill>.one-page.md` file next to the skill directory |

Flags are mutually exclusive. You can use only one at a time.

## Examples

```bash
# Copy to clipboard (default)
skill-bundler ~/.agents/skills/codebase-design

# See output in terminal
skill-bundler ~/.agents/skills/codebase-design -t

# Write to a file
skill-bundler ~/.agents/skills/codebase-design -o
```

## Output Structure

The generated Markdown contains:

- Title and source URI
- Structure Map (ASCII directory tree)
- `SKILL.md` content
- Language-tagged code fences for all non-hidden, non-binary text files
- List of skipped binary / undecodable files (without raw content)

## Project Structure

```
skill-bundler/
├── CONTEXT.md               # Domain glossary & ubiquitous language
├── README.md                # User guide & documentation
├── pyproject.toml           # Package configuration & console script entrypoint
├── src/
│   └── skill_bundler/       # Core Python package
│       ├── __init__.py
│       ├── __main__.py      # python -m skill_bundler entrypoint
│       ├── bundler.py       # Domain logic: parser, tree generator, bundler
│       ├── cli.py           # CLI argument parsing & output dispatch
│       └── clipboard.py     # OS clipboard adapter
└── skill_bundler.py         # Backward-compatible script wrapper
```

## Behavior Notes

- Excludes hidden files/directories (starting with `.`) and `__pycache__`.
- Skips symlinks to prevent recursion and external leakage.
- If the output file already exists (`-o`), the process halts with an error to prevent accidental overwrites.