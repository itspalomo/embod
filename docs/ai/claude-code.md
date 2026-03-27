# Embod With Claude Code

Claude Code support in this repo is implemented with:

- [CLAUDE.md](/Users/itspalomo/embod/CLAUDE.md)
- project skills in
  [.claude/skills](/Users/itspalomo/embod/.claude/skills)
- a project planning subagent at
  [.claude/agents/embod-planner.md](/Users/itspalomo/embod/.claude/agents/embod-planner.md)

## Recommended Usage

- use `/embod-design` for new Embod modeling work
- use `/embod-validate <path>` after edits
- use `@embod-planner` when requirements are incomplete

## Example Queries

```text
/embod-design
Design a PETG enclosure around this battery pack.
Ask me for any missing dimensions, mounting interfaces, and print constraints
before you edit code.
```

```text
@embod-planner
Plan a diff-drive robot embodiment in Embod and ask the minimum questions needed
before implementation.
```

```text
/embod-validate examples/diff_drive_robot.py
Then explain any warnings and show me the most useful snapshot.
```

Claude Code should prefer the same CLI loop documented in
[docs/ai/agent-workflow.md](/Users/itspalomo/embod/docs/ai/agent-workflow.md).
