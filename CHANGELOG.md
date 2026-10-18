# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Renamed
- Renamed the project from `skill-bundler` to `bundium` (package `skill_bundler` → `bundium`, CLI `bundium`; `skill-bundler` kept as a deprecated console-script alias). The name no longer cages the tool to skills: any folder of Markdown files can be packed into one self-contained document.

## [0.2.1] - 2026-09-24

### Removed
- Removed dead `validate_output` post-hoc string checks from the pack builder; the builder already guarantees structural output
- Removed unused `SKILL_MARKER_COMMENT` constant from the constants module
- Removed redundant re-parse fallback in the collection document builder; entry body is used directly

## [0.2.0] - 2026-09-24

### Added
- `index` subcommand that bundles a whole collection of skills into a single Markdown survey document, with a Skill Index table followed by each skill's `SKILL.md` body (see spec 0001)
- `--recursive` flag for `index` to include skills nested below immediate children
- Delivery flags for `index` mirroring `pack`: clipboard by default, `--terminal` for stdout, `--output` for a `.one-page.md` file next to the collection
