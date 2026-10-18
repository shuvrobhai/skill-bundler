# Testing & Quality Assurance

## Tooling

- **Test Runner**: Python standard library `unittest`, invoked via `uv run python -m unittest`.
- **Test Location**: `tests/` directory, mirroring the domain modules (`test_bundler.py`, `test_unpacker.py`, `test_indexer.py`).
- **Linting/Formatting**: none enforced — stdlib-only, no third-party linters.

## CI/CD vs Local

Bundium has no CI/CD pipeline. Tests run identically in any local environment; there are no environment-variable differences or platform-specific mocks. Clipboard tests are designed to run headless by mocking `bundium.cli.paste_from_clipboard` and `bundium.clipboard.*`.

## Commands

| Command | Purpose |
| --- | --- |
| `uv run python -m unittest discover -s tests` | Run the full test suite |
| `uv run python -m unittest tests.test_bundler -v` | Run one module |
| `uv run python -m unittest tests.test_unpacker.TestUnpacker.<test> -v` | Run one test |

## Test Categories

### Unit Tests

Unit tests cover each domain module's rules:

- **`test_bundler.py`** — file collection, Structure Map rendering, binary detection, code fence widening, nested `SKILL.md` preservation.
- **`test_unpacker.py`** — bundle parsing, path safety, collision guard, title sanitization, round-trip contract.
- **`test_indexer.py`** — skill discovery, recursive pruning, Skill Index rendering, description truncation and escaping.

### Integration / Round-Trip Tests

The keystone test is `tests/test_unpacker.py::test_round_trip_pack_and_unpack`. It packs a skill directory, unpacks the resulting bundle, and asserts the reconstructed directory matches the original.

**Any change to `bundler.py`, `unpacker.py`, or `bundle_format.py` must keep this test green.**

### Manual Verification

Manual checks are documented inline with the CLI:

```bash
# Pack a real skill and inspect the output
uv run bundium pack /path/to/skill -t | head -40

# Unpack it back
uv run bundium unpack /tmp/skill.one-page.md -d /tmp/skill-restored --force

# Survey a collection
uv run bundium index /path/to/collection -t | head -40