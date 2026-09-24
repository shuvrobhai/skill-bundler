---
name: custom-agent-scaffolding
description: Use when creating, structuring, or debugging custom agents and subagents in Google Antigravity (agy 1.1.12). Use when validating manifests, discovery, permissions, execution modes, or test paths.
---

# Custom Agent Scaffolding and Optimization

## Steps

### 1. Design the agent
Apply [Design process](#design-process).  
**Completion criterion:** Core intent, persona, system prompt, model, execution policy, identifier, and 2–4 description examples are specified.

### 2. Write the manifest
Apply [Manifest frontmatter](#manifest-frontmatter).  
**Completion criterion:** `name` and `description` are present; every tool in `tools` matches [Tool vocabulary](#tool-vocabulary); model and `commandExecutionPolicy` are set; prompt length is 500–3000 characters.

### 3. Configure permissions
Apply [Permission rules](#permission-rules).  
**Completion criterion:** Every command the agent needs is allowed in `settings.json`; `write_file`/`read_file` implication checked; sandbox scope matches execution policy.

### 4. Validate
Apply [Validation checklist](#validation-checklist).  
**Completion criterion:** Every checklist item passes; no tool mismatch that could hang initialization.

### 5. Test
Apply [Discovery and execution modes](#discovery-and-execution-modes).  
**Completion criterion:** Agent appears in TUI; workspace agent runs headlessly with explicit path; global agent runs by name; execution mode behaves as intended.

## Reference

### Design process
1. Extract core intent: what problem the agent solves.
2. Design expert persona: domain knowledge, constraints, output format.
3. Write system prompt with boundaries, process, edge cases, output schema.
4. Choose model and execution policy. Use `pro` for reasoning-heavy work, `flash` for fast triage, `sandbox` for review agents, `auto` for test or build agents.
5. Create identifier in lowercase kebab-case, 3–50 characters.
6. Write 2–4 description examples covering explicit requests, implicit needs, proactive triggers, and tool usage patterns.

### Manifest frontmatter
| Property | Type | Required | Default | Notes |
|---|---|---|---|---|
| name | string | yes | none | Unique ID; lowercase kebab-case; starts and ends alphanumerically |
| description | string | yes | none | Start with "Use when..." to guide the planner |
| tools | string[] | no | `[]` | Exact tool names; a misspelled name can hang the subagent |
| mainAgent | boolean | no | `true` | Allow manual selection as primary in interactive chat |
| subagent | boolean | no | `true` | Allow programmatic spawning through `invoke_subagent` |
| model | string | no | `inherit` | `inherit`, `flash`, or `pro` |
| commandExecutionPolicy | string | no | `sandbox` | `sandbox`, `auto`, `eager`, or `off` |
| mcpServers | object[] | no | `[]` | MCP servers exclusive to this agent |
| skills | string[] | no | `[]` | Skill dependencies |
| plugins | string[] | no | `[]` | Plugin dependencies |

Legacy properties `hidden` and `inheritMcp` are not supported.

### Execution policy modes
- `sandbox` isolates execution with kernel-level containment such as `nsjail`, `sandbox-exec`, or `AppContainer`. Missing sandbox capability fails closed with a hard error.
- `auto` runs safe, non-destructive operations like linters and local test compilations in the background. Risky commands such as `rm -rf` or forced pushes are gated for review.
- `eager` runs commands without prompting. Use only in trusted environments or CI.
- `off` disables command-line tools. Every `run_command` attempt is rejected.

### Permission rules
- `command` entries use anchored regex per token. `command(npm run (build.*))` matches `npm run build` and `npm run build-prod`.
- `write_file` implies `read_file` for the same path. Denying `read_file` blocks `write_file`.
- `unsandboxed(prefix)` lets a command run outside the sandbox.
- Interactive permission prompts allow editing file, URL, and MCP targets to expand scope. Command targets are not editable.

### Tool vocabulary
Use exact Antigravity tool names:

| Tool | What it does |
|---|---|
| view_file | Read a file |
| write_to_file | Create or overwrite a file |
| replace_file_content | Replace part of a file |
| multi_replace_file_content | Replace multiple parts of a file |
| grep_search | Search file contents |
| list_dir | List directories |
| find_by_name | Find files by name |
| run_command | Run shell commands, including git |
| invoke_subagent | Spawn another agent |

Grant only tools the agent actually needs. A read-only triage agent should have `view_file`, `grep_search`, `list_dir`, and possibly `run_command` for git diff. It should not have `write_to_file` or `invoke_subagent`.

### Discovery and execution modes
Where an agent gets discovered depends on how you run the CLI.

| Surface | Scanned paths | Behavior |
|---|---|---|
| Interactive TUI `/agents` | `.agents/agents/`, `~/.gemini/config/agents/`, `plugins/*/agents/` | Shows all discovered global, workspace, and plugin agents |
| Headless mode `agy -p --agent <name>` | `~/.gemini/config/agents/`, global plugins | Discovers global agents only; workspace-scoped agents are ignored by name |

Headless fallback warning: an unknown or workspace-scoped name silently falls back to the default agent. No error is thrown.

To run a workspace agent headlessly without fallback risk, pass the explicit manifest path.

```bash
agy -p "run audit" --agent .agents/agents/my-agent/agent.md
```

### Directory layout
Use the directory-centric pattern to bundle optional agent-scoped assets.

```
.agents/agents/my-agent/
├── agent.md
├── skills/
├── rules/
└── workflows/
```

Flat files like `.agents/agents/my-agent.md` still work for backward compatibility.

The `/agents` panel displays exact template locations:

```
Workspace: {workspace}/.agents/agents/{agent_name}/agent.md
Global: ~/.gemini/config/agents/{agent_name}/agent.md
```

Agent files must live inside the `agents/` directory. Manifests placed directly in config roots fail discovery loops.

### Subagent lifecycle states
- **running** — active and cancellable with Stop Subagent or `K`.
- **idle** — concluded current turn, paused; retains conversation memory and working filesystem.
- **done** — completed successfully; marked with a green checkmark.
- **error** — terminal failure, unhandled tool exception, or script hook timeout.
- **killed** — manually terminated; working directories, git branches, and containers cleaned; transcripts kept.

### System prompt guidelines
The markdown body after the frontmatter is the agent's core system prompt.

1. Define role, stack constraints, architectural limits, and output schema.
2. Write positive, action-oriented instructions. Use "Provide line-anchored annotations" instead of "Do not omit line numbers."
3. Reference only tools that appear in the frontmatter `tools` list.
4. Keep the prompt between 500 and 3000 characters. Point to separate `rules/*.md` or `GEMINI.md` files for long reference material.

### Description rules
The description is the most important field for delegation. Write 2–4 concrete examples. Each example includes:

- context of use
- developer prompt or trigger
- assistant action and tool pattern
- boundary case where the agent must not be selected

```
<example>
Context: User has completed a feature
user: "I've finished the authentication module"
assistant: "I'll use the code-quality-reviewer agent to check for bugs and security issues."
<commentary>
Auth code is high risk. Trigger the review agent.
</commentary>
</example>
```

Cover explicit requests, implicit needs, proactive triggers, and tool usage patterns. Be specific about when not to use the agent.

### Validation checklist
Run these checks before relying on an agent.

- Open `/agents` and confirm the agent appears in Available Agents.
- For global or plugin agents, run `agy agents` and check the list.
- Audit tool names: every entry in `tools` must match the exact system vocabulary.
- Check JSON payloads in the system prompt: every example JSON must close with a single brace to avoid parser issues.
- Confirm `name` follows kebab-case rules.
- Confirm `description` starts with "Use when..." and includes 2–4 examples.
- Confirm required frontmatter fields `name` and `description` are present.
- Confirm optional fields are set explicitly.
- Confirm model is `inherit`, `flash`, or `pro`.
- Confirm `mainAgent` and `subagent` are correct.
- Confirm `commandExecutionPolicy` fits the agent.
- Confirm process steps mention exact tools.
- Confirm output format is defined.
- Confirm edge cases are addressed.
- Confirm permissions in `settings.json` allow the commands the agent needs.

### Testing commands
Test workspace agents with explicit paths.

```bash
agy -p "run audit" --agent .agents/agents/<name>/agent.md
```

Test global agents by name.

```bash
agy -p "run audit" --agent <name>
```

Test workspace inheritance with `inherit`, `branch`, and `share` through `invoke_subagent`.

Execution modes affect file operations during testing:

- `agy --mode=default` pauses for diff review before file writes.
- `agy --mode=accept-edits` auto-approves file writes; subagents inherit this setting.
- `agy --mode=plan` prepends `/plan` and makes the agent investigate read-only before editing.
- Press `Shift+Tab` in the prompt box to cycle modes during a session.
- Set `agentMode` in `settings.json` to persist a default mode.

### TUI panel and keybindings
- Open the panel with `/agents` in the TUI.
- Available Agents lists the default agent and all discovered custom agents. Use arrow keys to select and Enter to prepare. Press Esc to apply the selection.
- Switching agents forks the conversation; it does not modify the current turn history.
- Subagents section groups background agents by triggering prompt. Press Enter on a group header to expand or collapse.
- Press Enter on a subagent row to open detail view with full thoughts, tool calls, and stdout. Press Esc to return.
- Press `K` on a running subagent to kill it. `K` does nothing on done or error subagents.
- Inline approval prompts appear in the panel. Press `A` to approve or `D` to deny.

Shortcuts:

- `Alt+J` teleports from the prompt to the next subagent waiting for approval.
- `Ctrl+K` fast-approves the pending action shown in the status notification.

TUI documentation typo warning: some legacy docs list `Ctrl+J` for teleport. `Ctrl+J` is reserved for inserting newlines in multi-line prompt boxes. `Alt+J` is the correct teleport binding.

For non-agent background shell processes, use `/tasks` instead of `/agents`.

### Transcript paths
Use the correct platform directory when writing hooks or scripts that audit conversation logs.

| Platform | Transcript path |
|---|---|
| Antigravity CLI (`agy`) | `~/.gemini/antigravity-cli/brain/<conversation_id>/.system_generated/logs/transcript.jsonl` |
| Antigravity 2.0 Desktop | `~/.gemini/antigravity/brain/<conversation_id>/.system_generated/logs/transcript.jsonl` |
| Antigravity IDE | `~/.gemini/antigravity-ide/brain/<conversation_id>/.system_generated/logs/transcript.jsonl` |

Target `antigravity-cli` for terminal-first sessions.

### AI-assisted generation
Use this prompt to generate an agent config from a description.

```
Create an agent configuration based on this request: "[YOUR DESCRIPTION]"

Requirements:
1. Extract core intent and responsibilities.
2. Design an expert persona for the domain.
3. Create a system prompt with clear behavioral boundaries, specific methodologies, edge case handling, and an output format.
4. Create an identifier in lowercase with hyphens, 3 to 50 characters.
5. Write a description with triggering conditions and 2 to 3 example blocks.
6. Return JSON with identifier, whenToUse, and systemPrompt.
```

### Workflow integration
Agents work inside workflows, skills, hooks, sidecars, plugins, and artifacts. A workflow can chain several agents.

```
# .agents/workflows/code-triage.md
---
description: Run full code review triage
---

1. Invoke change-expectation-agent with branch-diff mode to find business logic risks.
2. Invoke change-impact-agent to rate by blast radius.
3. Invoke change-failure-agent to find silent failures.
4. Invoke bug-hunter to do root cause analysis on critical files from step 3.
5. Generate implementation-plan artifact for fixes; require explicit approval unless artifactReviewPolicy is always-proceed.
```

Artifacts support asynchronous collaboration. Transcripts persist in the platform-specific brain path.

### Examples

#### code-auditor
```yaml
---
name: code-auditor
description: Use when security audits, static analysis, or code quality reviews are needed. Use when reviewing authentication, input validation, secret handling, or memory management.
tools:
  - view_file
  - grep_search
  - run_command
subagent: true
mainAgent: false
model: pro
commandExecutionPolicy: sandbox
skills:
  - skills/security-checklist
---

# System Prompt
You are an expert security auditor and code reviewer. Inspect source code for security vulnerabilities, memory leaks, and anti-patterns.

# Review Guidelines
1. Perform thorough static analysis without altering files unless explicitly asked.
2. Flag potential injection flaws, unvalidated inputs, or hardcoded secrets.
3. Provide concise, actionable remediation steps for each finding.
```

#### buffy
```yaml
---
name: buffy
description: Use when parallel subagent orchestration or high-velocity code modification is needed. Use for multi-file refactoring, test running, or deep codebase research.
tools:
  - view_file
  - replace_file_content
  - multi_replace_file_content
  - write_to_file
  - grep_search
  - find_by_name
  - run_command
  - invoke_subagent
mainAgent: true
subagent: true
model: pro
commandExecutionPolicy: sandbox
---

# System Prompt
You are Buffy, an enthusiastic coding assistant. Approach every problem with positivity and encouragement.

# Tone
- Use cheerful, friendly language.
- Be concise: prefer a single sentence when possible.
- Let actions and deliverables speak; end turns promptly when the task is complete.

# Orchestration
- Spawn parallel subagents with `invoke_subagent` for complex or parallelizable tasks.
- Provide each subagent with architectural context, symbol references, and goals.
- Track state with an `implementation_plan.md` artifact in the workspace.
- Use read-only tools first during audits.
- State what you are doing and execute the tool call immediately.
- Verify changes with sandboxed tests before declaring a goal complete.
```

## Fallback
- If a workspace agent name falls back silently in headless mode, pass the explicit manifest path.
- If a tool name is unmapped, replace it with the exact name from [Tool vocabulary](#tool-vocabulary).
- If sandbox capability is missing, execution fails closed; switch to `auto` or `eager` only in trusted environments or CI.
- If context overloads, point to separate `rules/*.md` or `GEMINI.md` files instead of inlining long reference material.
- If transcript path lookup fails, use the platform-specific path for the active Antigravity surface.