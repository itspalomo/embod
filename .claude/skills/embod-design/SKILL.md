---
name: embod-design
description: Design or refine Embod CADQuery projects. Use for new printable parts, assemblies, robot embodiment models, or when converting natural-language mechanical requirements into embod_project.py. Ask clarifying questions before editing when key measurements, units, interfaces, materials, or export targets are missing.
---

Use this skill for Embod authoring work.

## Clarification Gate

Before writing geometry, confirm any missing details that would materially change
the model:

- units and target dimensions
- vendor component model or interface standard
- hole pattern, shaft size, bearing size, or clearance targets
- print process, material, and build volume
- whether the user wants `stl`, `step`, `urdf`, snapshots, or simulation checks

If critical inputs are missing, stop and ask direct questions first.

## Plan-First Workflow

For assemblies and robots:

1. Summarize what is known.
2. List missing physical constraints.
3. Propose named `parts`, `assemblies`, `links`, `joints`, `frames`, and
   `interfaces`.
4. Only then edit code.

If the task is broad or ambiguous, prefer using the `embod-planner` agent or
Claude Code’s planning flow before editing.

## Embod Authoring Rules

- Keep geometry in `mm` and mass in `kg`.
- Register every manufacturable or robot-meaningful object in the project graph.
- Prefer `PrintProfile`, `InterfaceDef`, and `CollisionDef`.
- Keep fabrication entities separate from robot semantics.
- Make assumptions explicit in comments or in the response.

## Verification Loop

After editing a project:

1. `embod inspect <project> --json`
2. `embod validate <project> --json`
3. `embod build <project> --json`
4. Export requested artifacts.
5. Generate at least one relevant snapshot.

## Supporting Files

- Use [measurement-checklist.md](measurement-checklist.md) to decide which
  questions to ask before modeling.
- Use [examples.md](examples.md) for example prompts and task shapes.
