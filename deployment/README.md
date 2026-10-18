# Release & Distribution

> **Note**: Bundium has no server, container, or cloud infrastructure. This document covers how releases are versioned, packaged, and distributed.

## Deployment Overview

Bundium is a stdlib-only Python package. There are two distribution paths:

1. **Editable install** for local development: `uv sync` or `pip install -e .`.
2. **Source distribution / wheel** for release, published to PyPI (or any package index).

There is no hosted service, no Terraform, no Docker, and no CI/CD pipeline.

## Application Packaging

Bundium ships as a standard Python package built from the `src/` layout:

- **Build backend**: `setuptools >= 61`.
- **Package metadata**: `pyproject.toml`.
- **Entry point**: the `bundium` console script (`bundium = bundium.cli:main`), plus `python -m bundium`.

## Prerequisites

- Python 3.9+
- `uv` (recommended) or `pip`
- Build tools (`setuptools >= 61`, `build`) for producing distributions

## By Script

Local install (editable):

```bash
uv sync
# or:
pip install -e .
```

Build distributions:

```bash
uv run python -m build
```

## Release Process

1. **Update the version** in both `pyproject.toml` and `bundium.__version__` (they move together).
2. **Update `CHANGELOG.md`** following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.
3. **Write release notes** at `docs/releases/<version>.md`.
4. **Run the full test suite**:

   ```bash
   uv run python -m unittest discover -s tests
   ```

5. **Commit and tag**:

   ```bash
   git commit -am "Release v<version>"
   git tag v<version>
   git push origin main --tags
   ```

6. **Publish** to PyPI (when applicable):

   ```bash
   uv run python -m build
   uv run twine upload dist/*
   ```

## Versioning

Bundium follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html). The version lives in two places that must stay in sync:

| Location | Field |
| --- | --- |
| `pyproject.toml` | `[project] version` |
| `src/bundium/__init__.py` | `__version__` |

Git tags are `v<version>` (e.g. `v0.2.1`).

## CI/CD

Bundium has no CI/CD pipeline. Tests are run manually before tagging; the release process above is the complete workflow.