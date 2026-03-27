# Example Queries

These are high-signal prompts for agent clients working with Embod.

## Clarification-First Part Design

```text
Design a PETG wall mount for a Raspberry Pi Camera Module 3 in Embod.
Ask me for any missing dimensions, hole spacing, cable clearance, and print
constraints before writing code.
```

```text
I need a printable bracket for a NEMA17 motor and a GT2 idler.
Start in planning mode, confirm the mounting pattern and shaft geometry, then
propose the part graph before you implement it.
```

## Robot Embodiment Planning

```text
Plan a small diff-drive robot in Embod.
Do not guess wheel diameter, battery size, or motor model.
Ask the minimum questions needed, then propose parts, assemblies, links,
joints, and exports.
```

```text
I want a sensor mast for a rover chassis that can export to URDF and STL.
Clarify the sensor model, mounting interface, allowable height, and cable
routing before you edit anything.
```

## Validate And Iterate

```text
Validate this Embod project, explain all diagnostics, export the STEP for the
main part, and generate a CAD snapshot so I can compare intent against reality.
```

```text
Refine this Embod project for 3D printing.
If a missing tolerance or measurement blocks the work, stop and ask me before
editing.
```

## Tool-Specific Shortcuts

### Codex

```text
Use the project instructions in AGENTS.md.
Start in a planning pass and ask clarifying questions for any missing physical
dimensions before writing code.
```

### Claude Code

```text
/embod-design
Design a camera bracket for a 2020 extrusion rail. Ask me for missing
measurements first.
```

```text
@embod-planner Plan a mower chassis embodiment in Embod and list the minimum
questions needed before implementation.
```

### Cursor

```text
Use Ask or a custom Plan mode first.
Plan an Embod robot base and stop to ask me about wheel diameter, motor SKU,
and build volume before editing.
```
