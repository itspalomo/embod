from __future__ import annotations

from pathlib import Path

import cadquery as cq

from embod.model.manifest import (
    BuildManifest,
    CollisionManifest,
    SnapshotMetadata,
    SnapshotRecord,
)
from embod.runtime import ensure_dir, write_json
from embod.sim.pybullet_runner import capture_snapshot as capture_sim_snapshot


def _camera_preset(
    view: str,
) -> tuple[
    tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]
]:
    presets = {
        "iso": ((1.4, 1.4, 1.1), (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
        "front": ((0.0, -2.0, 0.2), (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
        "top": ((0.0, 0.0, 2.2), (0.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        "right": ((2.0, 0.0, 0.2), (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
        "sim_iso": ((1.4, 1.4, 1.1), (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    }
    if view not in presets:
        raise KeyError(f"Unknown camera preset {view}")
    return presets[view]


def _find_part_mesh(manifest: BuildManifest, subject: str) -> Path:
    for part in manifest.parts:
        if part.name == subject:
            return Path(
                next(item.path for item in part.exports if item.format == "stl")
            )
    for asset in manifest.assets:
        if asset.name == subject:
            match = next(
                (item.path for item in asset.exports if item.format == "stl"), None
            )
            return Path(match if match is not None else asset.path)
    for assembly in manifest.assemblies:
        if assembly.name == subject:
            return Path(
                next(item.path for item in assembly.exports if item.format == "glb")
            )
    raise KeyError(f"Unknown visual subject {subject}")


def _render_paths(
    mesh_paths: list[tuple[Path, str]],
    output_path: Path,
    *,
    view: str,
) -> SnapshotMetadata:
    import pyvista as pv

    plotter = pv.Plotter(off_screen=True, window_size=(960, 720))
    plotter.set_background("#f6f3ef")
    for mesh_path, color in mesh_paths:
        mesh = pv.read(str(mesh_path))
        plotter.add_mesh(mesh, color=color, show_edges=False, opacity=1.0)
    camera_position, focal_point, view_up = _camera_preset(view)
    plotter.camera_position = [camera_position, focal_point, view_up]
    ensure_dir(output_path.parent)
    plotter.show(screenshot=str(output_path), auto_close=False)
    plotter.close()
    return SnapshotMetadata(
        scene="cad",
        subject=output_path.stem,
        view=view,
        camera_position=camera_position,
        camera_target=focal_point,
        image_size=(960, 720),
    )


def _collision_shape(collision: CollisionManifest, path: Path) -> Path:
    ensure_dir(path.parent)
    if collision.kind == "box" and collision.size_mm is not None:
        x_mm, y_mm, z_mm = collision.size_mm
        shape = cq.Workplane().box(x_mm, y_mm, z_mm)
    elif (
        collision.kind == "cylinder"
        and collision.radius_mm is not None
        and collision.length_mm is not None
    ):
        shape = cq.Workplane().cylinder(collision.length_mm, collision.radius_mm)
    elif collision.kind == "sphere" and collision.radius_mm is not None:
        diameter = collision.radius_mm * 2.0
        shape = cq.Workplane().box(diameter, diameter, diameter)
    else:
        raise ValueError(f"Unsupported collision shape {collision.kind}")
    shape.export(str(path))
    return path


def _collision_meshes(
    manifest: BuildManifest, subject: str, temp_dir: Path
) -> list[tuple[Path, str]]:
    for robot in manifest.robots:
        if robot.name == subject:
            meshes: list[tuple[Path, str]] = []
            for link in robot.links:
                if link.collision is not None:
                    collision_path = _collision_shape(
                        link.collision,
                        temp_dir / f"{link.name}_collision.stl",
                    )
                    meshes.append((collision_path, "#d9534f"))
            return meshes
        for link in robot.links:
            if link.name == subject and link.collision is not None:
                return [
                    (
                        _collision_shape(
                            link.collision, temp_dir / f"{link.name}_collision.stl"
                        ),
                        "#d9534f",
                    )
                ]
    raise KeyError(f"Unknown collision subject {subject}")


def create_snapshot(
    manifest: BuildManifest,
    *,
    scene: str,
    subject: str,
    view: str,
    output_path: Path,
) -> SnapshotRecord:
    ensure_dir(output_path.parent)
    metadata_path = output_path.with_suffix(".json")
    if scene == "sim":
        image_path = capture_sim_snapshot(manifest, subject, output_path=output_path)
        metadata = SnapshotMetadata(
            scene=scene,
            subject=subject,
            view=view,
            camera_position=(1.6, 1.6, 1.1),
            camera_target=(0.0, 0.0, 0.0),
            image_size=(960, 720),
        )
    elif scene == "cad":
        mesh_path = _find_part_mesh(manifest, subject)
        metadata = _render_paths([(mesh_path, "#4f6d7a")], output_path, view=view)
        image_path = output_path
    elif scene == "collision":
        mesh_paths = _collision_meshes(manifest, subject, output_path.parent / "_temp")
        metadata = _render_paths(mesh_paths, output_path, view=view)
        image_path = output_path
    else:
        raise KeyError(f"Unknown scene {scene}")
    write_json(metadata_path, metadata)
    return SnapshotRecord(
        scene=scene,
        subject=subject,
        view=view,
        image_path=str(image_path),
        metadata_path=str(metadata_path),
    )
