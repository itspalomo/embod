from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.etree.ElementTree import Element, parse

import cadquery as cq

from embod.model.manifest import BuildManifest
from embod.runtime import ensure_dir


@dataclass(slots=True, frozen=True)
class SimulationResult:
    robot_name: str
    urdf_path: str
    steps: int
    link_count: int
    joint_count: int


def _resolve_urdf(manifest: BuildManifest, robot_name: str) -> Path:
    robot = next(item for item in manifest.robots if item.name == robot_name)
    record = next(item for item in robot.exports if item.format == "urdf")
    return Path(record.path)


def _parse_urdf(urdf_path: Path) -> Element[str]:
    root = parse(urdf_path).getroot()
    if root is None:
        raise RuntimeError(f"URDF {urdf_path} does not contain a root element")
    return root


def smoke_test_robot(
    manifest: BuildManifest,
    robot_name: str,
    *,
    steps: int,
) -> SimulationResult:
    urdf_path = _resolve_urdf(manifest, robot_name)
    root = _parse_urdf(urdf_path)
    link_names = {element.attrib["name"] for element in root.findall("link")}
    joint_elements = root.findall("joint")
    for joint in joint_elements:
        parent = joint.find("parent")
        child = joint.find("child")
        if parent is None or child is None:
            raise RuntimeError(
                f"Joint {joint.attrib.get('name', 'unknown')} is missing parent/child"
            )
        if parent.attrib["link"] not in link_names:
            raise RuntimeError(f"Joint parent link {parent.attrib['link']} is missing")
        if child.attrib["link"] not in link_names:
            raise RuntimeError(f"Joint child link {child.attrib['link']} is missing")
    for mesh in root.findall(".//mesh"):
        filename = mesh.attrib["filename"]
        if not Path(filename).exists():
            raise RuntimeError(f"URDF mesh is missing on disk: {filename}")
    return SimulationResult(
        robot_name=robot_name,
        urdf_path=str(urdf_path),
        steps=steps,
        link_count=len(link_names),
        joint_count=len(joint_elements),
    )


def capture_snapshot(
    manifest: BuildManifest,
    robot_name: str,
    *,
    output_path: Path,
    width: int = 960,
    height: int = 720,
) -> Path:
    import pyvista as pv

    robot = next(item for item in manifest.robots if item.name == robot_name)
    link_offsets: dict[str, tuple[float, float, float]] = {}
    root_links = {link.name for link in robot.links} - {
        joint.child for joint in robot.joints
    }
    for root_link in root_links:
        link_offsets[root_link] = (0.0, 0.0, 0.0)
    pending = True
    while pending:
        pending = False
        for joint in robot.joints:
            if joint.parent in link_offsets and joint.child not in link_offsets:
                parent_offset = link_offsets[joint.parent]
                link_offsets[joint.child] = (
                    parent_offset[0] + joint.origin_xyz_mm[0],
                    parent_offset[1] + joint.origin_xyz_mm[1],
                    parent_offset[2] + joint.origin_xyz_mm[2],
                )
                pending = True
    plotter = pv.Plotter(off_screen=True, window_size=(width, height))
    plotter.set_background("#f2efe8")
    temp_dir = ensure_dir(output_path.parent / "_sim_temp")
    for link in robot.links:
        if link.collision is None:
            continue
        shape = _collision_workplane(link.collision)
        offset = link_offsets.get(link.name, (0.0, 0.0, 0.0))
        translated = shape.translate(
            (
                offset[0] + link.collision.origin_xyz_mm[0],
                offset[1] + link.collision.origin_xyz_mm[1],
                offset[2] + link.collision.origin_xyz_mm[2],
            )
        )
        collision_path = temp_dir / f"{link.name}.stl"
        translated.export(str(collision_path))
        plotter.add_mesh(
            pv.read(str(collision_path)), color="#6c8c5a", show_edges=False
        )
    plotter.camera_position = [
        (1400.0, 1400.0, 1100.0),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
    ]
    ensure_dir(output_path.parent)
    plotter.show(screenshot=str(output_path), auto_close=False)
    plotter.close()
    return output_path


def _collision_workplane(collision: object) -> cq.Workplane:
    from embod.model.manifest import CollisionManifest

    if not isinstance(collision, CollisionManifest):
        raise TypeError("Collision data must be a CollisionManifest")
    if collision.kind == "box" and collision.size_mm is not None:
        x_mm, y_mm, z_mm = collision.size_mm
        return cq.Workplane().box(x_mm, y_mm, z_mm)
    if (
        collision.kind == "cylinder"
        and collision.radius_mm is not None
        and collision.length_mm is not None
    ):
        return cq.Workplane().cylinder(collision.length_mm, collision.radius_mm)
    if collision.kind == "sphere" and collision.radius_mm is not None:
        diameter = collision.radius_mm * 2.0
        return cq.Workplane().box(diameter, diameter, diameter)
    raise ValueError(f"Unsupported collision shape {collision.kind}")
