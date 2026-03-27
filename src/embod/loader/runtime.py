from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from types import ModuleType

from embod.exporters.cadquery_export import export_assembly, export_asset, export_part
from embod.exporters.urdf import export_urdf
from embod.model.core import CollisionDef, Project
from embod.model.manifest import (
    BuildManifest,
    BuildMetadata,
    BuildOutputs,
    CollisionManifest,
    ExportRecord,
    FrameManifest,
    InterfaceManifest,
    JointManifest,
    LinkManifest,
    RobotManifest,
    SensorManifest,
)
from embod.runtime import ensure_dir


def load_project_module(source_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("embod_user_project", source_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {source_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_project(module: ModuleType) -> Project:
    project = getattr(module, "project", None)
    if not isinstance(project, Project):
        raise RuntimeError(
            "Project entrypoint must expose a top-level `project = Project(...)`"
        )
    return project


def collision_manifest(collision: CollisionDef | None) -> CollisionManifest | None:
    if collision is None:
        return None
    return CollisionManifest(
        kind=collision.kind,
        size_mm=collision.size_mm,
        radius_mm=collision.radius_mm,
        length_mm=collision.length_mm,
        axis=collision.axis,
        mesh_asset=collision.mesh_asset,
        origin_xyz_mm=collision.origin_xyz_mm,
        origin_rpy_deg=collision.origin_rpy_deg,
    )


def build_manifest(
    source_path: Path, build_dir: Path, params: dict[str, str]
) -> BuildManifest:
    os.environ["EMBOD_PARAMS_JSON"] = json.dumps(params)
    ensure_dir(build_dir)
    module = load_project_module(source_path)
    project = resolve_project(module)
    part_manifests = [
        export_part(
            part,
            build_dir=build_dir,
            project=project,
            source_root=source_path.parent,
        )
        for part in project.parts.values()
    ]
    asset_manifests = [
        export_asset(asset, source_root=source_path.parent, build_dir=build_dir)
        for asset in project.imported_assets.values()
    ]
    assembly_manifests = [
        export_assembly(
            assembly,
            project=project,
            source_root=source_path.parent,
            build_dir=build_dir,
        )
        for assembly in project.assemblies.values()
    ]
    robots: list[RobotManifest] = []
    outputs: list[ExportRecord] = []
    for robot in project.robots.values():
        robot_manifest = RobotManifest(
            name=robot.name,
            links=[
                LinkManifest(
                    name=link.name,
                    parts=link.parts,
                    assemblies=link.assemblies,
                    collision=collision_manifest(link.collision),
                    inertial_proxy=collision_manifest(link.inertial_proxy),
                    mass_kg=link.mass_kg,
                    tags=link.tags,
                )
                for link in robot.links.values()
            ],
            joints=[
                JointManifest(
                    name=joint.name,
                    parent=joint.parent,
                    child=joint.child,
                    joint_type=joint.joint_type,
                    origin_xyz_mm=joint.origin_xyz_mm,
                    origin_rpy_deg=joint.origin_rpy_deg,
                    axis_xyz=joint.axis_xyz,
                    lower_limit_rad=joint.lower_limit_rad,
                    upper_limit_rad=joint.upper_limit_rad,
                )
                for joint in robot.joints.values()
            ],
            frames=[
                FrameManifest(
                    name=frame.name,
                    parent=frame.parent,
                    origin_xyz_mm=frame.origin_xyz_mm,
                    origin_rpy_deg=frame.origin_rpy_deg,
                )
                for frame in robot.frames.values()
            ],
            sensors=[
                SensorManifest(
                    name=sensor.name,
                    kind=sensor.kind,
                    frame=sensor.frame,
                    params=sensor.params,
                )
                for sensor in robot.sensors.values()
            ],
        )
        robots.append(robot_manifest)
    manifest = BuildManifest(
        metadata=BuildMetadata(
            project_name=project.name,
            units=project.units,
            source_path=str(source_path.resolve()),
            build_dir=str(build_dir.resolve()),
            params=params,
        ),
        interfaces=[
            InterfaceManifest(
                name=interface.name,
                kind=interface.kind,
                target=interface.target,
                origin_xyz_mm=interface.origin_xyz_mm,
                origin_rpy_deg=interface.origin_rpy_deg,
                surface_selector=interface.surface_selector,
                allowed_operation_kinds=interface.allowed_operation_kinds,
                clearance_mm=interface.clearance_mm,
                params=interface.params,
            )
            for interface in project.interfaces.values()
        ],
        parts=part_manifests,
        assets=asset_manifests,
        assemblies=assembly_manifests,
        robots=robots,
        outputs=BuildOutputs(
            manifest_path=str(build_dir / "manifest.json"),
            exports=outputs,
            snapshots=[],
        ),
    )
    robot_exports: list[RobotManifest] = []
    for robot_manifest in robots:
        urdf_path = export_urdf(manifest, robot_manifest.name, build_dir)
        export_record = ExportRecord(format="urdf", path=str(urdf_path))
        outputs.append(export_record)
        robot_exports.append(
            RobotManifest(
                name=robot_manifest.name,
                links=robot_manifest.links,
                joints=robot_manifest.joints,
                frames=robot_manifest.frames,
                sensors=robot_manifest.sensors,
                exports=[export_record],
            )
        )
    final_manifest = BuildManifest(
        metadata=manifest.metadata,
        interfaces=manifest.interfaces,
        parts=manifest.parts,
        assets=manifest.assets,
        assemblies=manifest.assemblies,
        robots=robot_exports,
        outputs=BuildOutputs(
            manifest_path=manifest.outputs.manifest_path,
            exports=outputs,
            snapshots=manifest.outputs.snapshots,
        ),
        schema_version=manifest.schema_version,
    )
    return final_manifest
