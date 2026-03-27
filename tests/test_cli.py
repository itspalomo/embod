from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from embod.cli.main import app


def test_new_and_inspect(tmp_path: Path) -> None:
    runner = CliRunner()
    project_dir = tmp_path / "demo"
    result = runner.invoke(app, ["new", str(project_dir), "--template", "part"])
    assert result.exit_code == 0
    source = project_dir / "embod_project.py"
    assert source.exists()
    inspect_result = runner.invoke(app, ["inspect", str(source), "--json"])
    assert inspect_result.exit_code == 0
    assert "bracket" in inspect_result.stdout
