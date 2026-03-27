from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path
from subprocess import CompletedProcess, run

from embod.model.manifest import BuildManifest
from embod.model.schema import JsonValue, SchemaModel


class CommandError(RuntimeError):
    pass


def build_hash(source_path: Path, params: dict[str, str]) -> str:
    payload = {
        "source": source_path.resolve().read_text(encoding="utf-8"),
        "params": params,
        "python": sys.version,
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def project_build_dir(source_path: Path, params: dict[str, str]) -> Path:
    return source_path.parent / ".embod" / "build" / build_hash(source_path, params)


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, model: SchemaModel | dict[str, JsonValue]) -> None:
    ensure_dir(path.parent)
    if isinstance(model, SchemaModel):
        path.write_text(model.model_dump_json(indent=2), encoding="utf-8")
        return
    path.write_text(json.dumps(model, indent=2, sort_keys=True), encoding="utf-8")


def read_manifest(path: Path) -> BuildManifest:
    return BuildManifest.model_validate_json(path.read_text(encoding="utf-8"))


def run_subprocess(args: list[str], cwd: Path) -> CompletedProcess[str]:
    completed = run(args, cwd=cwd, check=False, text=True, capture_output=True)
    if completed.returncode != 0:
        raise CommandError(completed.stderr.strip() or completed.stdout.strip())
    return completed


def copy_file(source: Path, target: Path) -> Path:
    ensure_dir(target.parent)
    shutil.copy2(source, target)
    return target
