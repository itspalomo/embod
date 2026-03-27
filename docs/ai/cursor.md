# Embod With Cursor

Cursor support in this repo is implemented through project rules in
[.cursor/rules](/Users/itspalomo/embod/.cursor/rules).

## What The Rules Enforce

- clarification-first behavior for underspecified physical designs
- Embod CLI usage instead of ad hoc guesswork
- explicit project-graph authoring for `embod_project.py` and example files

## Recommended Cursor Setup

The repo cannot check in your private Cursor custom mode settings, so configure
these manually in Cursor:

### Embod Plan

- Tools: codebase search, read file, terminal
- Instructions: ask clarifying questions before editing when dimensions, units,
  interfaces, or build constraints are missing; propose the Embod graph first

### Embod Build

- Tools: codebase search, read file, edit, terminal
- Instructions: after the plan is clear, edit the model and run `inspect`,
  `validate`, `build`, and a relevant `snapshot`

## Example Query

```text
Use the project rules for this repo.
Plan a camera mount in Embod and stop to ask me about missing dimensions,
fasteners, and print material before editing.
```

See
[docs/ai/example-queries.md](/Users/itspalomo/embod/docs/ai/example-queries.md)
for more prompt patterns.
