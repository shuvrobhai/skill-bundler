# 0005: Bundle Delimiter Integrity and Title Path Sanitization

Title sanitization and bundle file boundary extraction must prevent path traversal and delimiter collision. When unpacking without an explicit destination directory (`-d`), the destination defaults to `./<skill-title>/`, derived from `**Title:** One Page Version of <title>`. If `<title>` evaluates to `.` or `..`, sanitization that merely strips hyphens leaves relative traversal segments intact, escaping the working directory. Furthermore, splitting bundle contents via unanchored substring matching on `<!-- SOURCE: ... -->` and checking `_binary file — not inlined_` via broad substring containment causes self-referential markdown or documentation files to fragment or be dropped as binary files.

## Decision

1. **Title Traversal Guard**: `extract_skill_title` must reject or replace titles consisting solely of dots (`.`, `..`) or directory navigation tokens, falling back to the safe default `unpacked-skill`. `is_safe_relative_path` must reject path targets that resolve directly to the destination directory root (`dest == target_resolved`).
2. **Binary Skip Marker Precision**: `unpacker.py` will check for the binary placeholder using exact line equality (`content_body.strip() == "_binary file — not inlined_"`) rather than broad substring containment (`in content_body`), allowing source and test files to reference the marker string without being misclassified as binary assets.
3. **Delimiter Anchoring**: In-band delimiters (`<!-- SOURCE: <path> -->`) must be anchored to line boundaries (`(?m)^<!-- SOURCE:\s*(.*?)\s*-->$`) and validated against the bundle's Structure Map to prevent spurious splits from code examples or documentation.

## Consequences

- Self-referential skills (including `skill-bundler` itself) can be packaged and unpacked without data loss or section corruption.
- Untrusted bundles cannot manipulate destination directory resolution to escape the current working directory when `-d` is omitted.
- Backward compatibility with existing bundle documents is fully preserved.
