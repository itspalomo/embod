from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from embod.cli.main import app
from embod.model.diagnostics import DiagnosticsReport
from embod.runtime import project_build_dir, read_manifest


def test_new_and_inspect(tmp_path: Path) -> None:
    runner = CliRunner()
    project_dir = tmp_path / "demo"
    result = runner.invoke(app, ["new", str(project_dir), "--template", "part"])
    assert result.exit_code == 0
    source = project_dir / "embod_project.py"
    assert source.exists()
    contents = source.read_text(encoding="utf-8")
    assert "MeshProfile" in contents
    assert "fillet" in contents
    assert "cboreHole" in contents
    build_result = runner.invoke(app, ["build", str(source), "--json"])
    assert build_result.exit_code == 0
    manifest = json.loads(build_result.stdout)
    assert manifest["parts"][0]["name"] == "bracket"
    assert manifest["parts"][0]["mesh_profile"] == {
        "tolerance_mm": 0.03,
        "angular_tolerance_rad": 0.025,
    }


def test_default_mesh_profile_is_reported(tmp_path: Path) -> None:
    source = tmp_path / "embod_project.py"
    source.write_text(
        """
import cadquery as cq

from embod import Project

project = Project("mesh_defaults")

project.part(
    name="disk",
    geometry=cq.Workplane().circle(12.0).extrude(4.0),
)
""".strip()
        + "\n",
        encoding="utf-8",
    )
    runner = CliRunner()
    build_result = runner.invoke(app, ["build", str(source), "--json"])
    assert build_result.exit_code == 0
    manifest = json.loads(build_result.stdout)
    assert manifest["parts"][0]["mesh_profile"] == {
        "tolerance_mm": 0.05,
        "angular_tolerance_rad": 0.05,
    }
