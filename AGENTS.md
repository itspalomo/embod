# Embod Agent Instructions

Use this repository as a code-first mechanical design workspace.

## Scope

Embod projects describe:

- manufacturable parts and assemblies
- robot links, joints, frames, and sensors
- export and validation workflows through the `embod` CLI

Prefer working through the CLI and project graph instead of inventing ad hoc
CADQuery scripts outside the Embod model.

## Clarification First

When a user asks for a new part, assembly, or robot embodiment, do not guess
critical physical inputs.

Before writing or editing geometry, confirm missing high-impact details such as:

- units
- overall envelope or target dimensions
- hole spacing, fastener size, shaft size, bearing size, or vendor part model
- mating interfaces and clearances
- print process, material, and build volume
- load direction or structural constraints
- required outputs: `stl`, `step`, `urdf`, snapshots, or simulation checks

If any of those are missing and the answer would materially change geometry,
stay in planning/read-only mode and ask direct clarifying questions first.

## Default Workflow

For substantial design requests, use a plan-first loop:

1. Summarize known requirements.
2. List missing constraints as short, targeted questions.
3. Propose the intended project graph:
   `parts`, `assemblies`, `links`, `joints`, `frames`, `interfaces`.
4. Only then edit `embod_project.py` or related files.

For implementation and verification, prefer this CLI loop:

1. `embod inspect <project> --json`
2. `embod validate <project> --json`
3. `embod build <project> --json`
4. `embod export <project> --format ...`
5. `embod snapshot <project> --scene cad --subject ... --json`
6. `embod simulate <project> --smoke` when a robot is present

## Authoring Rules

- Use explicit `mm` geometry units in source models and `kg` for mass.
- Register all meaningful geometry in the project graph.
- Prefer `PrintProfile`, `InterfaceDef`, and `CollisionDef` over loose metadata.
- Do not hide assumptions. If a dimension or interface was inferred, say so.
- For robot models, keep manufacturable parts and robot semantics separate:
  parts/assemblies for fabrication, links/joints/frames for robotics.

## Validation Expectations

After editing an Embod model, verify at minimum:

- graph validation passes or expected warnings are explained
- exports requested by the user exist
- at least one snapshot matches the intended geometry

If validation fails because requirements are underspecified, report which
physical inputs are still missing.

## Prompt Style

Good design prompts explicitly allow clarification:

- “Design a PETG NEMA17 motor bracket. Ask for any missing measurements before
  writing code.”
- “Plan a diff-drive base in Embod. Confirm wheel diameter, motor model, and
  battery envelope before implementing.”
- “Refine this camera mount for 3D printing and show me a snapshot after the
  build.”

For more detail, see
[docs/ai/agent-workflow.md](/Users/itspalomo/embod/docs/ai/agent-workflow.md) and
[docs/ai/example-queries.md](/Users/itspalomo/embod/docs/ai/example-queries.md).
