from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from embod.cli.main import app
from embod.testing.fixtures import image_difference, load_fixture_assertions
from tests.support import ensure_step_asset


def _fixture_cases(root: Path) -> list[Path]:
    return sorted(item for item in root.iterdir() if item.is_dir())


def test_ai_fixture_harness(fixture_root: Path, tmp_path: Path) -> None:
    runner = CliRunner()
    for case_dir in _fixture_cases(fixture_root):
        if case_dir.name == "imported_mount":
            ensure_step_asset(case_dir / "fixture_asset.step")
        assertions = load_fixture_assertions(case_dir / "assertions.yaml")
        project_file = case_dir / "embod_project.py"
        inspect_result = runner.invoke(app, ["inspect", str(project_file), "--json"])
        assert inspect_result.exit_code == 0, inspect_result.stdout
        build_result = runner.invoke(app, ["build", str(project_file), "--json"])
        assert build_result.exit_code == 0, build_result.stdout
        validate_result = runner.invoke(app, ["validate", str(project_file), "--json"])
        assert validate_result.exit_code == 0, validate_result.stdout
        assert assertions.expected_project_name in build_result.stdout
        for diagnostic_code in assertions.required_diagnostic_codes:
            assert diagnostic_code in validate_result.stdout
        for part_name in assertions.expected_parts:
            assert part_name in build_result.stdout
        for export_format in assertions.required_export_formats:
            export_args = ["export", str(project_file), "--format", export_format]
            if assertions.expected_parts:
                export_args.extend(["--part", assertions.expected_parts[0]])
            if export_format == "urdf" and assertions.expected_robots:
                export_args.extend(["--robot", assertions.expected_robots[0]])
            export_result = runner.invoke(app, export_args)
            assert export_result.exit_code == 0, export_result.stdout
        for expected in assertions.snapshots:
            snapshot_name = (
                f"{case_dir.name}_{expected.subject}_"
                f"{expected.scene}_{expected.view}.png"
            )
            output_path = tmp_path / snapshot_name
            snapshot_result = runner.invoke(
                app,
                [
                    "snapshot",
                    str(project_file),
                    "--scene",
                    expected.scene,
                    "--subject",
                    expected.subject,
                    "--view",
                    expected.view,
                    "--output",
                    str(output_path),
                    "--json",
                ],
            )
            assert snapshot_result.exit_code == 0, snapshot_result.stdout
            approved = case_dir / "snapshots" / output_path.name
            assert approved.exists()
            assert image_difference(output_path, approved) <= 0.02
        if assertions.expected_robots and not assertions.required_diagnostic_codes:
            sim_result = runner.invoke(
                app, ["simulate", str(project_file), "--smoke", "--steps", "8"]
            )
            assert sim_result.exit_code == 0, sim_result.stdout
