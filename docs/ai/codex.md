# Embod With Codex

Use Embod as a local CLI tool, not as a hosted service.

Recommended loop:

1. `uv run embod capabilities --json`
2. `uv run embod inspect path/to/embod_project.py --json`
3. Edit `embod_project.py`
4. `uv run embod validate path/to/embod_project.py --json`
5. `uv run embod build path/to/embod_project.py --json`
6. `uv run embod export path/to/embod_project.py --format step`
7. `uv run embod snapshot path/to/embod_project.py --scene cad --subject bracket --json`
8. `uv run embod simulate path/to/embod_project.py --smoke`

Codex should prefer JSON output and explicit fixture assertions over free-form interpretation.
