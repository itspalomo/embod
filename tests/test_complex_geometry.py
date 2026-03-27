from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

from typer.testing import CliRunner

from embod.cli.main import app
from tests.support import ensure_step_asset, ensure_stl_asset


def _write_project(path: Path, source: str) -> Path:
    path.write_text(dedent(source).strip() + "\n", encoding="utf-8")
    return path


def test_build_manifest_records_auto_text_placement(tmp_path: Path) -> None:
    project_file = _write_project(
        tmp_path / "embod_project.py",
        """
        import cadquery as cq

        from embod import PrintProfile, Project, TextOp

        project = Project("auto_place_case")

        project.part(
            name="label_plate",
            geometry=cq.Workplane("XY").box(90.0, 40.0, 6.0),
            operations=[
                TextOp(
                    name="auto_label",
                    text="AUTO",
                    font_size_mm=14.0,
                    depth_mm=1.2,
                )
            ],
            print_profile=PrintProfile(
                process="fdm",
                material="PETG",
                orientation="flat",
                support_strategy="avoid",
            ),
            tags=["printable"],
        )
        """,
    )
    runner = CliRunner()
    result = runner.invoke(app, ["build", str(project_file), "--json"])
    assert result.exit_code == 0, result.stdout
    manifest = json.loads(result.stdout)
    operation = manifest["parts"][0]["operations"][0]
    assert operation["selected_placement"]["strategy"] == "auto"
    assert operation["selected_placement"]["selector"] == ">Z"
    assert manifest["parts"][0]["resolved_source_kind"] == "native_cadquery"


def test_build_manifest_records_interface_support_on_step_asset(tmp_path: Path) -> None:
    ensure_step_asset(tmp_path / "fixture_asset.step")
    project_file = _write_project(
        tmp_path / "embod_project.py",
        """
        from embod import (
            FeaturePlacement,
            GeometrySource,
            PrintProfile,
            Project,
            SupportOp,
        )

        project = Project("step_anchor_case")

        project.asset(
            name="camera_block",
            path="fixture_asset.step",
            kind="step",
            tags=["vendor"],
        )
        project.interface(
            name="mount_anchor",
            kind="mount_face",
            target="camera_block",
            origin_xyz=(0.0, 0.0, 4.0),
            surface_selector=">Z",
            allowed_operation_kinds=["support"],
            clearance_mm=1.5,
        )
        project.part(
            name="camera_adapter",
            geometry=GeometrySource.imported_step("camera_block"),
            operations=[
                SupportOp(
                    name="multiboard_adapter",
                    style="multiboard",
                    width_mm=14.0,
                    height_mm=10.0,
                    thickness_mm=4.0,
                    hole_diameter_mm=3.0,
                    hole_spacing_mm=8.0,
                    placement=FeaturePlacement(interface="mount_anchor"),
                )
            ],
            print_profile=PrintProfile(process="fdm", material="PETG"),
            tags=["printable"],
        )
        """,
    )
    runner = CliRunner()
    result = runner.invoke(app, ["build", str(project_file), "--json"])
    assert result.exit_code == 0, result.stdout
    manifest = json.loads(result.stdout)
    operation = manifest["parts"][0]["operations"][0]
    assert operation["selected_placement"]["strategy"] == "interface"
    assert operation["selected_placement"]["interface"] == "mount_anchor"
    assert manifest["parts"][0]["resolved_source_kind"] == "imported_step"


def test_validate_reports_placement_failures(tmp_path: Path) -> None:
    project_file = _write_project(
        tmp_path / "embod_project.py",
        """
        import cadquery as cq

        from embod import FeaturePlacement, PrintProfile, Project, TextOp

        project = Project("bad_place_case")

        project.part(
            name="fragile_plate",
            geometry=cq.Workplane("XY").box(24.0, 12.0, 2.0),
            operations=[
                TextOp(
                    name="oversized",
                    text="TOO BIG",
                    font_size_mm=10.0,
                    depth_mm=1.2,
                    mode="engrave",
                    placement=FeaturePlacement(
                        surface_selector=">Z",
                        min_clearance_mm=3.0,
                    ),
                ),
                TextOp(
                    name="too_deep",
                    text="I",
                    font_size_mm=4.0,
                    depth_mm=1.6,
                    mode="engrave",
                    placement=FeaturePlacement(surface_selector=">Z"),
                ),
            ],
            print_profile=PrintProfile(
                process="fdm",
                material="PLA",
                orientation="flat",
            ),
            tags=["printable"],
        )
        """,
    )
    runner = CliRunner()
    result = runner.invoke(app, ["validate", str(project_file), "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    codes = {item["code"] for item in payload["diagnostics"]}
    assert "placement.insufficient_clearance" in codes
    assert "placement.insufficient_thickness" in codes


def test_validate_phase_gates_stl_modifications(tmp_path: Path) -> None:
    ensure_stl_asset(tmp_path / "fixture_asset.stl")
    project_file = _write_project(
        tmp_path / "embod_project.py",
        """
        from embod import (
            FeaturePlacement,
            GeometrySource,
            PrintProfile,
            Project,
            SupportOp,
        )

        project = Project("stl_case")

        project.asset(name="mesh_block", path="fixture_asset.stl", kind="stl")
        project.part(
            name="mesh_wrapper",
            geometry=GeometrySource.imported_stl("mesh_block"),
            operations=[
                SupportOp(
                    name="gate",
                    style="multiboard",
                    width_mm=8.0,
                    height_mm=8.0,
                    thickness_mm=3.0,
                    placement=FeaturePlacement(surface_selector=">Z"),
                )
            ],
            print_profile=PrintProfile(process="fdm", material="PETG"),
            tags=["printable"],
        )
        """,
    )
    runner = CliRunner()
    build_result = runner.invoke(app, ["build", str(project_file), "--json"])
    assert build_result.exit_code == 0, build_result.stdout
    manifest = json.loads(build_result.stdout)
    assert manifest["parts"][0]["exports"] == [
        {
            "format": "stl",
            "path": manifest["parts"][0]["exports"][0]["path"],
        }
    ]
    validate_result = runner.invoke(app, ["validate", str(project_file), "--json"])
    assert validate_result.exit_code == 0, validate_result.stdout
    payload = json.loads(validate_result.stdout)
    codes = {item["code"] for item in payload["diagnostics"]}
    assert "mesh.phase_gated_stl_mods" in codes


def test_capabilities_report_includes_complex_geometry_flags() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["capabilities", "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["extras"]["text"] is True
    assert payload["extras"]["brep_mods"] is True
    assert payload["extras"]["mesh_mods"] is False
    assert payload["extras"]["placement"] is True
