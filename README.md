# Embod

Embod is a Python-first CADQuery toolchain for AI-assisted embodiment work. A
single project graph can describe manufacturable parts, assemblies, and robot
metadata, then export STL, STEP, URDF, reports, and deterministic snapshots
from the CLI.

## Status

This repository contains the MVP:

- Typed Python project model with `Project`, `Part`, `Assembly`, `Robot`,
  `Link`, `Joint`, `Frame`, `Sensor`, `InterfaceDef`, `PrintProfile`, and
  `CollisionDef`
- `embod` CLI with inspect/build/validate/export/preview/snapshot/simulate
  workflows
- Strict quality gates using `uv`, `ruff`, `mypy --strict`, and `pytest`
- Fixture-driven tests that simulate AI-authored projects and validate exports,
  diagnostics, and snapshots

## Install

Embod ships a console script named `embod`. Install it once from the repo
root:

```bash
uv tool install --python 3.11 --editable '.[full]'
```

That keeps the source checkout editable while exposing `embod` on your `PATH`.
Embod targets Python 3.11, and `uv` will download it automatically if needed.
If `uv` warns that its tool bin directory is missing from `PATH`, run:

```bash
uv tool update-shell
```

For a smaller install that skips snapshot rendering extras, use:

```bash
uv tool install --python 3.11 --editable .
```

`uv build` is for packaging wheels and source distributions, not the normal way
to run the CLI. Use it when you want artifacts in `dist/`, then install a built
wheel with `uv tool install --python 3.11 dist/*.whl`.

## Quickstart

```bash
embod new demo-bot --template robot
embod inspect demo-bot/embod_project.py --json
embod validate demo-bot/embod_project.py --json
embod build demo-bot/embod_project.py --json
embod export demo-bot/embod_project.py --format urdf
embod snapshot demo-bot/embod_project.py --scene cad --subject robot_visual --json
embod simulate demo-bot/embod_project.py --smoke
```

## Quality Bar

- No `Any` in `src/` or `tests/`
- No global `ignore_missing_imports`
- No lint/type suppressions as an escape hatch
- Optional dependencies are wrapped behind typed adapters

## AI Workflow

AI clients should prefer the machine-readable CLI:

1. `embod capabilities --json`
2. `embod inspect <project> --json`
3. Edit `embod_project.py`
4. `embod validate <project> --json`
5. `embod build <project> --json`
6. `embod export <project> --format step`
7. `embod snapshot <project> --scene cad --subject <part-or-assembly> --json`
8. `embod simulate <project> --smoke`

This repo now also ships tool-native agent guidance:

- [AGENTS.md](/Users/itspalomo/embod/AGENTS.md) for Codex and generic agent clients
- [CLAUDE.md](/Users/itspalomo/embod/CLAUDE.md),
  [.claude/skills](/Users/itspalomo/embod/.claude/skills), and
  [.claude/agents](/Users/itspalomo/embod/.claude/agents) for Claude Code
- [.cursor/rules](/Users/itspalomo/embod/.cursor/rules) for Cursor

Client-specific guidance lives in
[docs/ai/codex.md](/Users/itspalomo/embod/docs/ai/codex.md),
[docs/ai/claude-code.md](/Users/itspalomo/embod/docs/ai/claude-code.md),
[docs/ai/cursor.md](/Users/itspalomo/embod/docs/ai/cursor.md),
[docs/ai/agent-workflow.md](/Users/itspalomo/embod/docs/ai/agent-workflow.md),
[docs/ai/example-queries.md](/Users/itspalomo/embod/docs/ai/example-queries.md),
and
[docs/ai/tool-support.md](/Users/itspalomo/embod/docs/ai/tool-support.md).
