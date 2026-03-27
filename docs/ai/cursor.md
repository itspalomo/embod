# Embod With Cursor

Cursor agents should use the local CLI and commit generated Python project files, not opaque binaries.

Recommended contract:

- `embod inspect --json` for graph discovery
- `embod validate --json` for diagnostics
- `embod build --json` to materialize canonical artifacts
- `embod snapshot --json` for visual regression checks
