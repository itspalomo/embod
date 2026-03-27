# Embod Claude Code Guide

Use the project-specific Embod workflow when the task involves CADQuery,
mechanical design, printable parts, or robot embodiment.

## Default Behavior

- Ask clarifying questions before editing if key measurements, interfaces, or
  fabrication constraints are missing.
- Prefer planning before implementation for any multi-part or robot request.
- Use the `embod` CLI for inspection, validation, build, export, and snapshots.

## Project Skills And Agents

Use these project-level Claude Code assets when relevant:

- `/embod-design`
  Use for new parts, assemblies, robot embodiment work, or refactors of
  `embod_project.py`.
- `/embod-validate <path-to-embod_project.py>`
  Use after edits to run the standard validation and artifact loop.
- `@embod-planner`
  Use when requirements are incomplete and the task needs clarification-first
  planning.

The detailed workflow and example prompts live in:

- [docs/ai/agent-workflow.md](/Users/itspalomo/embod/docs/ai/agent-workflow.md)
- [docs/ai/example-queries.md](/Users/itspalomo/embod/docs/ai/example-queries.md)
