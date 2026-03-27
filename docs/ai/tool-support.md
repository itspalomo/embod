# AI Tool Support

This repo now ships agent guidance in the formats that the major coding clients
actually support.

## What Is Implemented Here

- Codex and generic agent clients:
  [AGENTS.md](/Users/itspalomo/embod/AGENTS.md)
- Claude Code:
  [CLAUDE.md](/Users/itspalomo/embod/CLAUDE.md),
  [.claude/skills/embod-design/SKILL.md](/Users/itspalomo/embod/.claude/skills/embod-design/SKILL.md),
  [.claude/skills/embod-validate/SKILL.md](/Users/itspalomo/embod/.claude/skills/embod-validate/SKILL.md),
  [.claude/agents/embod-planner.md](/Users/itspalomo/embod/.claude/agents/embod-planner.md)
- Cursor:
  [.cursor/rules/embod-core.mdc](/Users/itspalomo/embod/.cursor/rules/embod-core.mdc),
  [.cursor/rules/embod-project-files.mdc](/Users/itspalomo/embod/.cursor/rules/embod-project-files.mdc)

## Research Summary

- OpenAI documents `AGENTS.md` as a reliable way to steer Codex and other agent
  clients, and the Codex app supports reusable skills across the app, CLI, and
  IDE surfaces.
- Claude Code supports project `CLAUDE.md`, project skills in
  `.claude/skills/`, and project subagents in `.claude/agents/`.
- Cursor supports project rules in `.cursor/rules/*.mdc` and custom modes in
  Cursor settings. Custom modes are user-configured, so this repo documents
  recommended modes instead of checking in a private settings file.

## Recommended Cursor Custom Modes

Cursor custom modes are configured in the app, not committed as a stable repo
file. Recommended modes for Embod:

### Embod Plan

- Tools:
  codebase search, read file, terminal
- Instructions:
  ask clarifying questions before editing when dimensions, units, interfaces, or
  build constraints are missing; propose the Embod graph first

### Embod Build

- Tools:
  codebase search, read file, edit, terminal
- Instructions:
  after the plan is clear, edit the model and run `inspect`, `validate`,
  `build`, and a relevant `snapshot`

## Official References

- [OpenAI Codex app announcement](https://openai.com/index/introducing-the-codex-app/)
- [OpenAI Docs MCP guide](https://developers.openai.com/learn/docs-mcp)
- [Claude Code skills](https://docs.anthropic.com/en/docs/claude-code/slash-commands)
- [Claude Code subagents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)
- [Cursor rules](https://docs.cursor.com/en/context)
- [Cursor custom modes](https://docs.cursor.com/chat/custom-modes)
