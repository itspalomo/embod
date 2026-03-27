from __future__ import annotations

import json
import sys
from enum import StrEnum
from pathlib import Path

import typer
from rich.console import Console

from embod._version import __version__
from embod.model.diagnostics import DiagnosticsReport
from embod.model.manifest import (
    BuildManifest,
    CapabilitiesReport,
    FixtureAssertionSet,
)
from embod.runtime import project_build_dir, read_manifest, run_subprocess
from embod.validators.project import print_report, validate_manifest

app = typer.Typer(no_args_is_help=True, pretty_exceptions_show_locals=False)
console = Console()


class ExportFormat(StrEnum):
    STL = "stl"
    STEP = "step"
    URDF = "urdf"
    GLTF = "gltf"


class SnapshotScene(StrEnum):
    CAD = "cad"
    COLLISION = "collision"
    SIM = "sim"


JSON_OPTION = typer.Option(False, "--json")
PARAM_OPTION = typer.Option(None, "--param")
OUTPUT_OPTION = typer.Option(None, "--output")
FORMAT_OPTION = typer.Option(..., "--format")
SCENE_OPTION = typer.Option(..., "--scene")
SUBJECT_OPTION = typer.Option(..., "--subject")


def _parse_params(items: list[str] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise typer.BadParameter("Parameters must use key=value form")
        key, value = item.split("=", 1)
        result[key] = value
    return result


def _ensure_manifest(
    source: Path, params: dict[str, str], rebuild: bool
) -> BuildManifest:
    build_dir = project_build_dir(source, params)
    manifest_path = build_dir / "manifest.json"
    if rebuild or not manifest_path.exists():
        run_subprocess(
            [
                sys.executable,
                "-m",
                "embod.loader.runner",
                str(source.resolve()),
                str(build_dir.resolve()),
                json.dumps(params),
            ],
            cwd=source.parent,
        )
    return read_manifest(manifest_path)


def _emit_json(enabled: bool, payload: object) -> None:
    if enabled:
        console.print_json(json.dumps(payload))


def _template_contents(name: str, template: str) -> str:
    title = name.replace("-", "_")
    if template == "part":
        return f"""import cadquery as cq

from embod import MeshProfile, PrintProfile, Project

project = Project("{title}")

base = cq.Workplane("XY").box(68.0, 34.0, 6.0).edges("|Z").fillet(3.0)
upright = (
    cq.Workplane("XY")
    .box(68.0, 6.0, 42.0)
    .translate((0.0, 14.0, 18.0))
    .edges("|Z")
    .fillet(2.0)
)
left_gusset = (
    cq.Workplane("XZ")
    .polyline([(-22.0, 0.0), (-22.0, 24.0), (0.0, 0.0)])
    .close()
    .extrude(6.0)
    .translate((0.0, 7.0, 0.0))
)
right_gusset = (
    cq.Workplane("XZ")
    .polyline([(22.0, 0.0), (22.0, 24.0), (0.0, 0.0)])
    .close()
    .extrude(6.0)
    .translate((0.0, 7.0, 0.0))
)
bracket = base.union(upright).union(left_gusset).union(right_gusset)
bracket = (
    bracket.faces(">Z")
    .workplane()
    .pushPoints([(-20.0, 0.0), (20.0, 0.0)])
    .cboreHole(5.2, 10.0, 3.0)
)
bracket = (
    bracket.faces(">Y")
    .workplane()
    .pushPoints([(-18.0, 10.0), (18.0, 10.0)])
    .hole(4.3)
)

project.part(
    name="bracket",
    geometry=bracket,
    mesh_profile=MeshProfile(tolerance_mm=0.03, angular_tolerance_rad=0.025),
    print_profile=PrintProfile(
        process="fdm",
        material="PETG",
        layer_height_mm=0.2,
        nozzle_mm=0.4,
        orientation="flat",
        max_build_volume_mm=(256.0, 256.0, 256.0),
    ),
    tags=["printable", "structural"],
)
"""
    if template == "assembly":
        return f"""import cadquery as cq

from embod import AssemblyComponent, MeshProfile, PrintProfile, Project

project = Project("{title}")

base = (
    cq.Workplane("XY")
    .box(96.0, 64.0, 5.0)
    .edges("|Z")
    .fillet(6.0)
    .faces(">Z")
    .workplane()
    .pushPoints([(-32.0, -20.0), (-32.0, 20.0), (32.0, -20.0), (32.0, 20.0)])
    .circle(5.5)
    .extrude(16.0)
    .faces(">Z")
    .workplane(offset=16.0)
    .pushPoints([(-32.0, -20.0), (-32.0, 20.0), (32.0, -20.0), (32.0, 20.0)])
    .hole(3.2)
    .faces(">Z")
    .workplane()
    .rect(56.0, 28.0)
    .cutBlind(-3.0)
)
mast = (
    cq.Workplane("XY")
    .box(18.0, 42.0, 54.0)
    .translate((0.0, 0.0, 27.0))
    .edges("|Z")
    .fillet(2.0)
    .faces(">Y")
    .workplane()
    .pushPoints([(0.0, 14.0), (0.0, 30.0)])
    .hole(4.0)
)

base_plate = project.part(
    name="base_plate",
    geometry=base,
    mesh_profile=MeshProfile(tolerance_mm=0.04, angular_tolerance_rad=0.035),
    print_profile=PrintProfile(process="fdm", material="PETG"),
    tags=["printable", "structural"],
)

sensor_mast = project.part(
    name="sensor_mast",
    geometry=mast,
    mesh_profile=MeshProfile(tolerance_mm=0.03, angular_tolerance_rad=0.025),
    print_profile=PrintProfile(process="fdm", material="PETG"),
    tags=["printable"],
)

project.assembly(
    name="demo_assembly",
    components=[
        AssemblyComponent(name="base_plate_instance", ref=base_plate.name),
        AssemblyComponent(
            name="sensor_mast_instance",
            ref=sensor_mast.name,
            translation_mm=(0.0, 0.0, 2.5),
        ),
    ],
)
"""
    return f"""import cadquery as cq

from embod import (
    AssemblyComponent,
    CollisionDef,
    MeshProfile,
    PrintProfile,
    Project,
)

project = Project("{title}")
robot = project.robot("{title}")

wheel = project.part(
    name="wheel",
    geometry=(
        cq.Workplane("XZ")
        .circle(32.0)
        .extrude(14.0, both=True)
        .faces(">Y")
        .workplane()
        .circle(24.0)
        .cutBlind(-6.0)
        .faces("<Y")
        .workplane()
        .circle(24.0)
        .cutBlind(-6.0)
        .faces(">Y")
        .workplane()
        .hole(8.0)
        .faces(">Y")
        .workplane()
        .pushPoints([(-14.0, 0.0), (14.0, 0.0), (0.0, 14.0), (0.0, -14.0)])
        .hole(10.0)
    ),
    mesh_profile=MeshProfile(tolerance_mm=0.02, angular_tolerance_rad=0.02),
    print_profile=PrintProfile(process="fdm", material="TPU"),
    tags=["printable", "wheel"],
)

chassis = project.part(
    name="chassis",
    geometry=(
        cq.Workplane("XY")
        .box(140.0, 88.0, 16.0)
        .edges("|Z")
        .fillet(10.0)
        .faces(">Z")
        .workplane()
        .rect(88.0, 52.0)
        .cutBlind(-8.0)
        .faces(">Z")
        .workplane()
        .pushPoints([(-46.0, -24.0), (-46.0, 24.0), (46.0, -24.0), (46.0, 24.0)])
        .circle(6.0)
        .extrude(12.0)
        .faces(">Z")
        .workplane(offset=12.0)
        .pushPoints([(-46.0, -24.0), (-46.0, 24.0), (46.0, -24.0), (46.0, 24.0)])
        .hole(3.2)
    ),
    mesh_profile=MeshProfile(tolerance_mm=0.04, angular_tolerance_rad=0.035),
    print_profile=PrintProfile(process="fdm", material="PETG"),
    tags=["printable", "structural"],
)

sensor_mast = project.part(
    name="sensor_mast",
    geometry=(
        cq.Workplane("XY")
        .box(18.0, 42.0, 54.0)
        .translate((0.0, 0.0, 27.0))
        .edges("|Z")
        .fillet(2.0)
        .faces(">Y")
        .workplane()
        .pushPoints([(0.0, 14.0), (0.0, 30.0)])
        .hole(4.0)
    ),
    mesh_profile=MeshProfile(tolerance_mm=0.03, angular_tolerance_rad=0.025),
    print_profile=PrintProfile(process="fdm", material="PETG"),
    tags=["printable", "sensor_mount"],
)

project.assembly(
    name="robot_visual",
    components=[
        AssemblyComponent(name="chassis_instance", ref=chassis.name),
        AssemblyComponent(
            name="left_wheel_instance",
            ref=wheel.name,
            translation_mm=(0.0, 62.0, -24.0),
        ),
        AssemblyComponent(
            name="right_wheel_instance",
            ref=wheel.name,
            translation_mm=(0.0, -62.0, -24.0),
        ),
        AssemblyComponent(
            name="sensor_mast_instance",
            ref=sensor_mast.name,
            translation_mm=(36.0, 0.0, 8.0),
        ),
    ],
)

robot.link(
    name="base_link",
    parts=[chassis.name, sensor_mast.name],
    assemblies=["robot_visual"],
    collision=CollisionDef.box(140.0, 88.0, 28.0),
    inertial_proxy=CollisionDef.box(140.0, 88.0, 28.0),
    mass_kg=2.1,
)
robot.link(
    name="left_wheel_link",
    parts=[wheel.name],
    collision=CollisionDef.cylinder(radius_mm=32.0, length_mm=28.0, axis="y"),
    mass_kg=0.35,
    tags=["wheel"],
)
robot.link(
    name="right_wheel_link",
    parts=[wheel.name],
    collision=CollisionDef.cylinder(radius_mm=32.0, length_mm=28.0, axis="y"),
    mass_kg=0.35,
    tags=["wheel"],
)

robot.joint(
    name="left_wheel_joint",
    parent="base_link",
    child="left_wheel_link",
    joint_type="continuous",
    origin_xyz=(0.0, 62.0, -24.0),
    axis_xyz=(0.0, 1.0, 0.0),
)
robot.joint(
    name="right_wheel_joint",
    parent="base_link",
    child="right_wheel_link",
    joint_type="continuous",
    origin_xyz=(0.0, -62.0, -24.0),
    axis_xyz=(0.0, 1.0, 0.0),
)

robot.frame(
    name="front_camera_frame",
    parent="base_link",
    origin_xyz=(54.0, 0.0, 62.0),
)
robot.sensor(
    name="front_camera",
    kind="rgbd",
    frame="front_camera_frame",
    params={{"hfov_deg": 92.0, "vfov_deg": 58.0}},
)
"""


@app.command()
def version() -> None:
    console.print(__version__)


@app.command()
def capabilities(json_output: bool = typer.Option(False, "--json")) -> None:
    viz_available = _module_available("pyvista")
    sim_available = True
    report = CapabilitiesReport(
        commands=[
            "new",
            "inspect",
            "build",
            "validate",
            "export",
            "preview",
            "snapshot",
            "bom",
            "print-report",
            "simulate",
            "doctor",
            "capabilities",
        ],
        export_formats=["stl", "step", "urdf", "glb"],
        snapshot_scenes=["cad", "collision", "sim"],
        extras={
            "viz": viz_available,
            "sim": sim_available,
        },
    )
    if json_output:
        _emit_json(True, report.model_dump())
    else:
        console.print(report.model_dump_json(indent=2))


@app.command()
def new(
    name: str,
    template: str = typer.Option("robot", "--template"),
) -> None:
    project_dir = Path(name).resolve()
    project_dir.mkdir(parents=True, exist_ok=True)
    source_path = project_dir / "embod_project.py"
    if source_path.exists():
        raise typer.BadParameter(f"{source_path} already exists")
    source_path.write_text(_template_contents(name, template), encoding="utf-8")
    console.print(f"Created [bold]{source_path}[/bold]")


@app.command()
def inspect(
    file: Path,
    json_output: bool = JSON_OPTION,
    param: list[str] | None = PARAM_OPTION,
) -> None:
    manifest = _ensure_manifest(file.resolve(), _parse_params(param), rebuild=True)
    payload = {
        "schema_version": "embod.inspect.v1",
        "project_name": manifest.metadata.project_name,
        "parts": [part.name for part in manifest.parts],
        "assemblies": [assembly.name for assembly in manifest.assemblies],
        "robots": [robot.name for robot in manifest.robots],
        "interfaces": [interface.name for interface in manifest.interfaces],
        "params": manifest.metadata.params,
    }
    if json_output:
        _emit_json(True, payload)
    else:
        console.print_json(json.dumps(payload))


@app.command()
def build(
    file: Path,
    json_output: bool = JSON_OPTION,
    param: list[str] | None = PARAM_OPTION,
) -> None:
    manifest = _ensure_manifest(file.resolve(), _parse_params(param), rebuild=True)
    if json_output:
        _emit_json(True, manifest.model_dump())
    else:
        console.print(
            f"Built {manifest.metadata.project_name} into {manifest.metadata.build_dir}"
        )


@app.command()
def validate(
    file: Path,
    json_output: bool = JSON_OPTION,
    checks: str = typer.Option("geometry,graph,print,robot", "--checks"),
    param: list[str] | None = PARAM_OPTION,
) -> None:
    _ = checks
    manifest = _ensure_manifest(file.resolve(), _parse_params(param), rebuild=True)
    report = validate_manifest(manifest)
    if json_output:
        _emit_json(True, report.model_dump())
    else:
        for diagnostic in report.diagnostics:
            rendered = (
                f"[{diagnostic.level}] {diagnostic.code}: "
                f"{diagnostic.message} ({diagnostic.subject})"
            )
            console.print(rendered)
        if not report.diagnostics:
            console.print("No diagnostics")


def _copy_export(
    manifest: BuildManifest, format_name: str, subject: str | None, output: Path | None
) -> Path:
    if subject is None:
        if format_name == "urdf" and manifest.robots:
            path = next(
                item.path
                for item in manifest.robots[0].exports
                if item.format == "urdf"
            )
            selected = Path(path)
        elif format_name in {"stl", "step"} and manifest.parts:
            selected = Path(
                next(
                    item.path
                    for item in manifest.parts[0].exports
                    if item.format == format_name
                )
            )
        elif format_name in {"gltf", "glb"} and manifest.assemblies:
            selected = Path(
                next(
                    item.path
                    for item in manifest.assemblies[0].exports
                    if item.format == "glb"
                )
            )
        else:
            raise typer.BadParameter(f"No exportable subject for format {format_name}")
    else:
        selected = _resolve_export_path(manifest, format_name, subject)
    destination = output.resolve() if output is not None else selected
    if destination != selected:
        destination.write_bytes(selected.read_bytes())
    return destination


def _resolve_export_path(
    manifest: BuildManifest, format_name: str, subject: str
) -> Path:
    for part in manifest.parts:
        if part.name == subject:
            return Path(
                next(item.path for item in part.exports if item.format == format_name)
            )
    for asset in manifest.assets:
        if asset.name == subject:
            return Path(
                next(item.path for item in asset.exports if item.format == format_name)
            )
    for assembly in manifest.assemblies:
        if assembly.name == subject:
            record = next(
                item for item in assembly.exports if item.format in {format_name, "glb"}
            )
            return Path(record.path)
    for robot in manifest.robots:
        if robot.name == subject:
            return Path(
                next(item.path for item in robot.exports if item.format == format_name)
            )
    raise typer.BadParameter(f"Unknown export subject {subject}")


@app.command()
def export(
    file: Path,
    format: ExportFormat = FORMAT_OPTION,
    part: str | None = typer.Option(None, "--part"),
    assembly: str | None = typer.Option(None, "--assembly"),
    robot: str | None = typer.Option(None, "--robot"),
    output: Path | None = OUTPUT_OPTION,
    param: list[str] | None = PARAM_OPTION,
) -> None:
    manifest = _ensure_manifest(file.resolve(), _parse_params(param), rebuild=True)
    subject = robot or assembly or part
    chosen_format = "glb" if format == ExportFormat.GLTF else format.value
    exported = _copy_export(manifest, chosen_format, subject, output)
    console.print(str(exported))


@app.command()
def snapshot(
    file: Path,
    scene: SnapshotScene = SCENE_OPTION,
    subject: str = SUBJECT_OPTION,
    view: str = typer.Option("iso", "--view"),
    output: Path | None = OUTPUT_OPTION,
    json_output: bool = JSON_OPTION,
    param: list[str] | None = PARAM_OPTION,
) -> None:
    from embod.viz.snapshot import create_snapshot

    manifest = _ensure_manifest(file.resolve(), _parse_params(param), rebuild=True)
    default_output = (
        Path(manifest.metadata.build_dir)
        / "snapshots"
        / f"{subject}_{scene.value}_{view}.png"
    )
    record = create_snapshot(
        manifest,
        scene=scene.value,
        subject=subject,
        view=view,
        output_path=output.resolve() if output is not None else default_output,
    )
    if json_output:
        _emit_json(True, record.model_dump())
    else:
        console.print(record.image_path)


@app.command()
def preview(
    file: Path,
    target: str = typer.Option("visual", "--target"),
    subject: str = SUBJECT_OPTION,
    open: bool = typer.Option(False, "--open"),
    param: list[str] | None = PARAM_OPTION,
) -> None:
    from embod.viz.snapshot import create_snapshot

    scene = "collision" if target == "collision" else "cad"
    manifest = _ensure_manifest(file.resolve(), _parse_params(param), rebuild=True)
    output = Path(manifest.metadata.build_dir) / "preview" / f"{subject}_{scene}.png"
    record = create_snapshot(
        manifest, scene=scene, subject=subject, view="iso", output_path=output
    )
    if open:
        run_subprocess(["open", record.image_path], cwd=file.parent.resolve())
    console.print(record.image_path)


@app.command("bom")
def bom_command(
    file: Path,
    json_output: bool = JSON_OPTION,
    param: list[str] | None = PARAM_OPTION,
) -> None:
    manifest = _ensure_manifest(file.resolve(), _parse_params(param), rebuild=True)
    payload = {
        "schema_version": "embod.bom.v1",
        "parts": [part.name for part in manifest.parts],
        "assets": [asset.name for asset in manifest.assets],
        "assemblies": [
            {
                "name": assembly.name,
                "components": [component.ref for component in assembly.components],
            }
            for assembly in manifest.assemblies
        ],
    }
    if json_output:
        _emit_json(True, payload)
    else:
        console.print_json(json.dumps(payload))


@app.command("print-report")
def print_report_command(
    file: Path,
    json_output: bool = JSON_OPTION,
    param: list[str] | None = PARAM_OPTION,
) -> None:
    manifest = _ensure_manifest(file.resolve(), _parse_params(param), rebuild=True)
    report = print_report(manifest)
    if json_output:
        _emit_json(True, report.model_dump())
    else:
        console.print_json(report.model_dump_json(indent=2))


@app.command()
def simulate(
    file: Path,
    smoke: bool = typer.Option(False, "--smoke"),
    steps: int = typer.Option(120, "--steps"),
    headless: bool = typer.Option(True, "--headless"),
    param: list[str] | None = PARAM_OPTION,
) -> None:
    from embod.sim.pybullet_runner import smoke_test_robot

    _ = headless
    manifest = _ensure_manifest(file.resolve(), _parse_params(param), rebuild=True)
    if not smoke:
        raise typer.BadParameter("Only --smoke is supported in the MVP")
    if not manifest.robots:
        raise typer.BadParameter("Project does not contain a robot")
    result = smoke_test_robot(manifest, manifest.robots[0].name, steps=steps)
    console.print_json(
        json.dumps(
            {
                "robot_name": result.robot_name,
                "urdf_path": result.urdf_path,
                "steps": result.steps,
                "links": result.link_count,
                "joints": result.joint_count,
            }
        )
    )


@app.command()
def doctor(
    file: Path | None = None,
    json_output: bool = JSON_OPTION,
) -> None:
    viz_available = _module_available("pyvista")
    payload = {
        "schema_version": "embod.doctor.v1",
        "python": sys.version.split()[0],
        "viz_extra": viz_available,
        "sim_extra": True,
        "file_exists": file.resolve().exists() if file is not None else True,
    }
    if json_output:
        _emit_json(True, payload)
    else:
        console.print_json(json.dumps(payload))


@app.command()
def schema(name: str) -> None:
    if name == "manifest":
        console.print(BuildManifest.model_json_schema())
        return
    if name == "diagnostics":
        console.print(DiagnosticsReport.model_json_schema())
        return
    if name == "fixture":
        console.print(FixtureAssertionSet.model_json_schema())
        return
    raise typer.BadParameter(f"Unknown schema {name}")


def main() -> None:
    app()


def _module_available(module_name: str) -> bool:
    try:
        __import__(module_name)
    except ImportError:
        return False
    return True
