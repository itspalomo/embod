from __future__ import annotations

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
    inspect_result = runner.invoke(app, ["inspect", str(source), "--json"])
    assert inspect_result.exit_code == 0
    assert "bracket" in inspect_result.stdout


def test_validate_filters_requested_checks(fixture_root: Path) -> None:
    runner = CliRunner()
    project_file = fixture_root / "oversized_print" / "embod_project.py"

    print_result = runner.invoke(
        app,
        ["validate", str(project_file), "--checks", "print", "--json"],
    )
    assert print_result.exit_code == 0
    print_report = DiagnosticsReport.model_validate_json(print_result.stdout)
    assert [item.code for item in print_report.diagnostics] == ["print.oversized_part"]

    graph_result = runner.invoke(
        app,
        ["validate", str(project_file), "--checks", "graph", "--json"],
    )
    assert graph_result.exit_code == 0
    graph_report = DiagnosticsReport.model_validate_json(graph_result.stdout)
    assert list(graph_report.diagnostics) == []


def test_snapshot_records_accumulate_in_manifest(
    fixture_root: Path, tmp_path: Path
) -> None:
    runner = CliRunner()
    project_file = fixture_root / "simple_bracket" / "embod_project.py"
    params: dict[str, str] = {}
    first_output = tmp_path / "bracket_iso.png"
    second_output = tmp_path / "bracket_front.png"

    first_result = runner.invoke(
        app,
        [
            "snapshot",
            str(project_file),
            "--scene",
            "cad",
            "--subject",
            "bracket",
            "--view",
            "iso",
            "--output",
            str(first_output),
            "--json",
        ],
    )
    assert first_result.exit_code == 0

    second_result = runner.invoke(
        app,
        [
            "snapshot",
            str(project_file),
            "--scene",
            "cad",
            "--subject",
            "bracket",
            "--view",
            "front",
            "--output",
            str(second_output),
            "--json",
        ],
    )
    assert second_result.exit_code == 0

    manifest = read_manifest(
        project_build_dir(project_file.resolve(), params) / "manifest.json"
    )
    records = {
        (item.scene, item.subject, item.view): item.image_path
        for item in manifest.outputs.snapshots
    }
    assert records[("cad", "bracket", "iso")] == str(first_output.resolve())
    assert records[("cad", "bracket", "front")] == str(second_output.resolve())
