from __future__ import annotations

from pathlib import Path

import cadquery as cq


def ensure_step_asset(path: Path) -> Path:
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.Workplane().box(20.0, 20.0, 8.0).export(str(path))
    return path
