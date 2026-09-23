# 0004: The Collection Bundle inlines SKILL.md only, and is not an unpack input

`skill-bundler index` produces one Markdown document for a whole Collection, and two things about
that document are deliberate rather than incidental: it inlines only each Skill's `SKILL.md`, and
`unpack` cannot read it back. Inlining every supporting file would have produced a 713,487 byte
document (~178k tokens) that no context window can absorb, where the 19 `SKILL.md` files alone are
already 185,893 bytes (~46k tokens), so the document answers "what Skills do I have" while `pack`
stays the way to get one Skill in full. `unpack` rejects it for free, because the document never
contains the literal `<!-- SOURCE: SKILL.md -->` marker that `unpack` requires as proof of a
genuine Bundle, and that is also why a `SKILL.md` sitting directly in the Collection directory is
never included: it would produce exactly that path and quietly make the document unpackable.

## Considered Options

- **Inline every text file of every Skill.** Rejected: ~178k tokens for this repository's own
  Collection, leaving no room in the context window for the conversation the document exists to
  support.
- **Emit only the Skill Index, with no bodies.** Rejected as the default, because it cannot answer
  "what does this Skill actually do". Left as a possible later `--index-only` flag.
- **Make the Collection Bundle round-trippable through `unpack`.** Rejected: it needs new rules
  for which directory each section belongs in, and the path safety guards would have to be
  re-derived for the nested case. A separate feature, not a free addition.

## Consequences

- `pack` remains the only way to reach a Skill's supporting files, so the two commands stay
  separable: `index` to survey, `pack` to use.
- The output carries no timestamp, so it is byte-identical across runs and can be diffed.
