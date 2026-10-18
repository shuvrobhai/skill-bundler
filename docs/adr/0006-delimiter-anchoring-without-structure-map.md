# 0006: Delimiter Anchoring Without Structure Map Reverse-Parsing

ADR-0005 introduced `parse_structure_map_paths` to cross-validate file section delimiters (`<!-- SOURCE: <path> -->`) against the `# Skill's Structure Map` ASCII tree. In practice, reverse-engineering directory hierarchies from ASCII tree characters (`[└├]──`) with 4-space depth arithmetic introduces fragile heuristics without security benefits: delimiters are already anchored to line boundaries (`(?m)^<!-- SOURCE:\s*(.*?)\s*-->$`) and verified against immediate Markdown section headers (`## <path>`). Furthermore, requiring paths to exist in the ASCII tree breaks bundles that omit the Structure Map or format it with different connector characters.

## Decision Outcome

Partially supersede ADR-0005. Section boundary detection in `bundle_format.deserialize` will rely exclusively on two-token pairing: a line-anchored delimiter comment (`(?m)^<!-- SOURCE:\s*(.*?)\s*-->$`) immediately followed by an identical heading (`## <path>`). Structure Map ASCII parsing is completely removed.

Decisions 1 (Title Traversal Guard) and 2 (Binary Skip Marker Precision) of ADR-0005 remain active and unchanged.

## Consequences

- Eliminates 32 lines of fragile regex and indentation parsing from `bundle_format.py`.
- Permits bundles with custom or absent Structure Maps to be unpacked safely.
- Retains title traversal guards and binary placeholder exact line checks from ADR-0005.
