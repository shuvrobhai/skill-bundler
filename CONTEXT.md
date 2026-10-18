# Bundium

A tool that packages a folder of Markdown files (e.g. an AI agent skill) into a single, self-contained document for easy sharing and pasting into LLM sessions.

## Language

**Skill**:
A modular folder containing an agent instruction file (`SKILL.md`) along with optional supporting scripts, examples, or reference resources.
_Avoid_: Plugin folder, tool package, agent folder

**Bundle**:
A single, self-contained Markdown document aggregating a Skill's metadata, directory structure, and text files.
_Avoid_: Package, archive, dump, one-page file

**Collection**:
A directory whose immediate children are Skill directories.
_Avoid_: Skills folder, skill library, catalog

**Collection Bundle**:
A single Markdown document aggregating every Skill in a Collection into one shareable file.
_Avoid_: Index file, multi-skill bundle, mega bundle

**SKILL.md**:
The root instruction and metadata markdown document required at the top level of every Skill.
_Avoid_: Manifest, skill config, readme

**Structure Map**:
A visual ASCII tree representation of the folders and files within a Skill directory.
_Avoid_: File list, directory graph, folder hierarchy

**Inlined File**:
A text file from the Skill embedded directly into the Bundle inside a language-tagged code fence.
_Avoid_: Embedded source, injected file, snippet

**Skipped File**:
A binary, undecodable, or excluded file noted by name in the Bundle without embedding raw content.
_Avoid_: Ignored file, omitted binary, filtered asset

**Delivery Target**:
The destination to which the final Bundle is delivered (System Clipboard, Terminal stdout, or File on disk).
_Avoid_: Output mode, export sink, print channel

**Unpack**:
The reverse operation that reads a Bundle and reconstructs the original Skill directory and inlined files on disk.
_Avoid_: Decompress, extract, restore, explode

