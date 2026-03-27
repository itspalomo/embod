# Embod Agent Workflow

This is the shared workflow the repo expects across Codex, Claude Code, and
Cursor.

## Use A Clarification Gate

Before editing geometry, confirm any missing detail that would materially change
the model:

- units
- critical dimensions
- interface standards or vendor part models
- clearances and tolerances
- print process, material, and build volume
- requested exports and verification steps

If the request is incomplete, ask focused questions first instead of
hallucinating geometry.

## Prefer Planning For New Designs

For anything larger than a trivial single part:

1. summarize what is known
2. list the missing physical inputs
3. propose the Embod graph
4. implement only after the graph and assumptions are clear

For robot projects, separate:

- parts and assemblies for manufacturing
- links, joints, frames, and sensors for robotics

## Standard CLI Loop

Use the local CLI as the primary interface:

```bash
embod inspect path/to/embod_project.py --json
embod validate path/to/embod_project.py --json
embod build path/to/embod_project.py --json
embod export path/to/embod_project.py --format step
embod snapshot path/to/embod_project.py --scene cad --subject bracket --json
embod simulate path/to/embod_project.py --smoke
```

## What Good Agent Behavior Looks Like

- ask for missing measurements early
- keep units explicit
- name graph entities clearly
- make assumptions visible
- verify with snapshots when shape or fit matters
- explain which warning is a real blocker and which is only advisory
