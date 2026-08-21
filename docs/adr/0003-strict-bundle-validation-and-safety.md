# 0003: Strict Bundle Validation and Path Traversal Safety

## Context and Problem Statement
Unpacking untrusted bundles from the clipboard or external sources introduces risks of corrupted skill directories or path traversal attacks (`../` relative paths attempting to write outside the target directory).

## Decision Outcome
The unpacker parses the complete bundle into an in-memory representation, validates that `SKILL.md` is present, ensures all relative paths are safe and contained within the target directory, and verifies code fence boundaries before touching the filesystem.

## Consequences
- Protects against malformed or malicious bundles before creating any directories or files.
- Atomic verification: either the entire skill unpacks cleanly or nothing is written.
