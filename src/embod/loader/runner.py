from __future__ import annotations

import json
import sys
from pathlib import Path

from embod.loader.runtime import build_manifest
from embod.runtime import write_json


def main() -> int:
    if len(sys.argv) != 4:
        raise SystemExit(
            "Usage: python -m embod.loader.runner <source> <build_dir> <params_json>"
        )
    source_path = Path(sys.argv[1]).resolve()
    build_dir = Path(sys.argv[2]).resolve()
    params = json.loads(sys.argv[3])
    if not isinstance(params, dict):
        raise SystemExit("params_json must decode to an object")
    normalized = {str(key): str(value) for key, value in params.items()}
    manifest = build_manifest(source_path, build_dir, normalized)
    write_json(build_dir / "manifest.json", manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
