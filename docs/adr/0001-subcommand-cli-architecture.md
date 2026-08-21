# 0001: Adopt Subcommand CLI Architecture with Backward-Compatible Default

## Context and Problem Statement
Adding bidirectional unpacking (unpacking bundles into skill directories) alongside bundling requires clear CLI semantics without breaking legacy usage (`skill-bundler /path/to/skill`).

## Decision Outcome
Adopt a subcommand architecture (`skill-bundler pack` and `skill-bundler unpack`). If the first positional argument is a directory path rather than a subcommand name, the CLI routes to `pack` by default to preserve seamless backward compatibility.

## Consequences
- Enables future commands (`skill-bundler validate`, `skill-bundler lint`) without flag collisions.
- Supports unpacking directly from clipboard (`skill-bundler unpack -c`) or from disk files (`skill-bundler unpack bundle.md`).
