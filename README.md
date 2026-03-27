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

## Quickstart

```bash
uv sync --all-extras --dev
uv run embod new demo-bot --template robot
uv run embod inspect demo-bot/embod_project.py --json
uv run embod validate demo-bot/embod_project.py --json
uv run embod build demo-bot/embod_project.py --json
uv run embod export demo-bot/embod_project.py --format urdf
uv run embod snapshot demo-bot/embod_project.py --scene cad --json
uv run embod simulate demo-bot/embod_project.py --smoke
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
7. `embod snapshot <project> --scene cad --json`
8. `embod simulate <project> --smoke`

Client-specific guidance lives in [docs/ai/codex.md](/Users/itspalomo/embod/docs/ai/codex.md),
[docs/ai/claude-code.md](/Users/itspalomo/embod/docs/ai/claude-code.md), and
[docs/ai/cursor.md](/Users/itspalomo/embod/docs/ai/cursor.md).
