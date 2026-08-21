# 0002: Safe Overwrite Guard on Unpack

## Context and Problem Statement
Unpacking a bundle could overwrite existing local files or scripts in an existing skill directory, causing accidental data loss.

## Decision Outcome
By default, the unpacker aborts and outputs a list of conflicting files if any target file already exists on disk. Users must explicitly pass the `--force` / `-f` flag to overwrite existing files.

## Consequences
- Prevents accidental destruction of uncommitted local modifications.
- Predictable behavior in automated scripts and non-interactive environments without hanging on interactive prompts.
