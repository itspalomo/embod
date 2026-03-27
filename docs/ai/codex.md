# Embod With Codex

Codex support in this repo is implemented through
[AGENTS.md](/Users/itspalomo/embod/AGENTS.md) plus the local `embod` CLI.

## Recommended Behavior

- start with a planning pass for new designs
- ask clarifying questions before editing when physical constraints are missing
- use the machine-readable CLI rather than free-form guessing
- use snapshots to compare intent against actual geometry

## Standard Loop

1. `uv run python -m embod capabilities --json`
2. `uv run python -m embod inspect path/to/embod_project.py --json`
3. Ask for missing measurements if needed.
4. Edit `embod_project.py`
5. `uv run python -m embod validate path/to/embod_project.py --json`
6. `uv run python -m embod build path/to/embod_project.py --json`
7. `uv run python -m embod export path/to/embod_project.py --format step`
8. `uv run python -m embod snapshot path/to/embod_project.py --scene cad --subject bracket --json`
9. `uv run python -m embod simulate path/to/embod_project.py --smoke`

## Example Prompt

```text
Use AGENTS.md for this repo.
Plan a printable wheel mount in Embod and ask me for any missing dimensions,
shaft details, bearing specs, or print constraints before writing code.
```

For shared workflow guidance, see
[docs/ai/agent-workflow.md](/Users/itspalomo/embod/docs/ai/agent-workflow.md)
and
[docs/ai/example-queries.md](/Users/itspalomo/embod/docs/ai/example-queries.md).
