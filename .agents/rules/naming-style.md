---
trigger: always_on
---

# Code Naming Conventions

Rules for naming variables, functions, classes, and constants in this repository.

## General

- Use full, descriptive words over abbreviations.
- Keep names specific to their purpose.
- Prefer positive, clear names that reveal intent.
- Use `snake_case` for variables, functions, and methods.
- Use `PascalCase` for class names.
- Use `UPPER_SNAKE_CASE` for constants.
- Avoid single-letter names except for loop counters (`i`, `j`, `k`).
- Avoid vague names like `data`, `info`, `temp`, `process`, or `x`.

## Boolean names

- Start boolean variables and function parameters with `is_`, `has_`, `can_`, or `should_`.
- Use `is_` for states or properties: `is_active`, `is_valid`, `is_binary`.
- Use `has_` for possession or inclusion: `has_permission`, `has_error`.
- Use `can_` for ability: `can_edit`, `can_delete`.
- Use `should_` for decisions and boolean parameters: `should_validate`, `should_render`, `should_overwrite: bool = False`.

## Functions

- Use a verb or verb phrase: `get_user`, `parse_skill`, `validate_output`.
- Name functions by what they do, not how they do it.
- If a function mutates state, include that in the name: `fetch_and_update_user_login`, not `get_user`.
- Use `_` prefix for private helpers, and ensure helpers are also verb phrases: `_render_tree_body`, `_build_code_fence`.

## Domain vocabulary alignment

- Prefer domain terms defined in `CONTEXT.md` for code identifiers:
  - Use `structure_map` over generic terms like `tree`, `file_list`, or `hierarchy`.
  - Use `bundle` over `archive`, `package`, or `dump`.
  - Use `collection` and `collection_bundle` for multi-skill sets.
  - Use `relative_path` or `file_path` over abbreviations like `rel` or `p`.

## Constants

- Use all uppercase with underscores: `MAX_RETRY_ATTEMPTS`.
- Include units or purpose when relevant: `CACHE_DURATION_MS`, `BINARY_PROBE_SIZE`.
- Replace magic numbers with named constants.

## Abbreviations

- Avoid uncommon abbreviations.
- Allow widely known abbreviations: `id`, `url`, `html`, `api`, `json`, `http`.
- Spell out shortened words when clarity improves: `relative_path` not `rel` or `rel_path`, `command` not `cmd`, `description` not `desc`.

## Files and modules

- Name Python files using `snake_case`: `skill_bundler.py`.
- Keep file names descriptive and aligned with the main class or purpose.
- Use `kebab-case` for rule file names: `naming.md`, `code-style.md`.

## Examples

```python
# Good
MAX_RETRY_ATTEMPTS = 3

def validate_email(email_address: str) -> bool:
    ...

def collect_skill_files(skill_dir: Path) -> list[Path]:
    ...

class SkillBundler:
    ...
```

```python
# Avoid
MAX = 100
def proc(data):
    ...
def validate(x):
    ...
```