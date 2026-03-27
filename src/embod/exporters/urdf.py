from __future__ import annotations

from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree, SubElement

from embod.model.manifest import BuildManifest, CollisionManifest
from embod.runtime import ensure_dir


def _mm_to_m(value_mm: float) -> float:
    return value_mm / 1000.0


def _xyz_mm_to_m(vector: tuple[float, float, float]) -> str:
    return " ".join(f"{_mm_to_m(item):.6f}" for item in vector)


def _rpy_deg_to_rad(vector: tuple[float, float, float]) -> str:
    from math import radians

    return " ".join(f"{radians(item):.6f}" for item in vector)


def _collision_geometry_xml(parent: Element, collision: CollisionManifest) -> None:
    geometry = SubElement(parent, "geometry")
    if collision.kind == "box" and collision.size_mm is not None:
        SubElement(
            geometry,
            "box",
            size=_xyz_mm_to_m(collision.size_mm),
        )
        return
    if (
        collision.kind == "cylinder"
        and collision.radius_mm is not None
        and collision.length_mm is not None
    ):
        SubElement(
            geometry,
            "cylinder",
            radius=f"{_mm_to_m(collision.radius_mm):.6f}",
            length=f"{_mm_to_m(collision.length_mm):.6f}",
        )
        return
    if collision.kind == "sphere" and collision.radius_mm is not None:
        SubElement(geometry, "sphere", radius=f"{_mm_to_m(collision.radius_mm):.6f}")
        return
    if collision.kind == "mesh" and collision.mesh_asset is not None:
        SubElement(geometry, "mesh", filename=collision.mesh_asset)


def _link_inertia(
    mass_kg: float, collision: CollisionManifest | None
) -> tuple[float, float, float]:
    if collision is None:
        fallback = mass_kg * 0.01
        return fallback, fallback, fallback
    if collision.kind == "box" and collision.size_mm is not None:
        x_m, y_m, z_m = (_mm_to_m(item) for item in collision.size_mm)
        ixx = mass_kg * (y_m**2 + z_m**2) / 12.0
        iyy = mass_kg * (x_m**2 + z_m**2) / 12.0
        izz = mass_kg * (x_m**2 + y_m**2) / 12.0
        return ixx, iyy, izz
    if (
        collision.kind == "cylinder"
        and collision.radius_mm is not None
        and collision.length_mm is not None
    ):
        radius_m = _mm_to_m(collision.radius_mm)
        length_m = _mm_to_m(collision.length_mm)
        radial = mass_kg * (3.0 * radius_m**2 + length_m**2) / 12.0
        axial = 0.5 * mass_kg * radius_m**2
        return radial, radial, axial
    if collision.kind == "sphere" and collision.radius_mm is not None:
        radius_m = _mm_to_m(collision.radius_mm)
        inertia = 0.4 * mass_kg * radius_m**2
        return inertia, inertia, inertia
    fallback = mass_kg * 0.01
    return fallback, fallback, fallback


def export_urdf(manifest: BuildManifest, robot_name: str, output_dir: Path) -> Path:
    robot = next(item for item in manifest.robots if item.name == robot_name)
    robot_dir = ensure_dir(output_dir / "robots" / robot_name)
    urdf_path = robot_dir / f"{robot_name}.urdf"
    root = Element("robot", name=robot_name)
    for link in robot.links:
        link_element = SubElement(root, "link", name=link.name)
        visuals = link.parts + link.assemblies
        for visual_name in visuals:
            visual = SubElement(link_element, "visual")
            geometry = SubElement(visual, "geometry")
            mesh_filename = _mesh_path(manifest, visual_name)
            SubElement(geometry, "mesh", filename=mesh_filename)
        if link.collision is not None:
            collision = SubElement(link_element, "collision")
            SubElement(
                collision,
                "origin",
                xyz=_xyz_mm_to_m(link.collision.origin_xyz_mm),
                rpy=_rpy_deg_to_rad(link.collision.origin_rpy_deg),
            )
            _collision_geometry_xml(collision, link.collision)
        if link.mass_kg is not None:
            inertial = SubElement(link_element, "inertial")
            SubElement(inertial, "origin", xyz="0 0 0", rpy="0 0 0")
            SubElement(inertial, "mass", value=f"{link.mass_kg:.6f}")
            inertia_proxy = link.inertial_proxy or link.collision
            ixx, iyy, izz = _link_inertia(link.mass_kg, inertia_proxy)
            SubElement(
                inertial,
                "inertia",
                ixx=f"{ixx:.6f}",
                ixy="0.0",
                ixz="0.0",
                iyy=f"{iyy:.6f}",
                iyz="0.0",
                izz=f"{izz:.6f}",
            )
    for joint in robot.joints:
        joint_element = SubElement(
            root, "joint", name=joint.name, type=joint.joint_type
        )
        SubElement(joint_element, "parent", link=joint.parent)
        SubElement(joint_element, "child", link=joint.child)
        SubElement(
            joint_element,
            "origin",
            xyz=_xyz_mm_to_m(joint.origin_xyz_mm),
            rpy=_rpy_deg_to_rad(joint.origin_rpy_deg),
        )
        SubElement(
            joint_element,
            "axis",
            xyz=" ".join(f"{item:.6f}" for item in joint.axis_xyz),
        )
        if joint.lower_limit_rad is not None and joint.upper_limit_rad is not None:
            SubElement(
                joint_element,
                "limit",
                lower=f"{joint.lower_limit_rad:.6f}",
                upper=f"{joint.upper_limit_rad:.6f}",
                effort="1.0",
                velocity="10.0",
            )
    ElementTree(root).write(urdf_path, encoding="utf-8", xml_declaration=True)
    return urdf_path


def _mesh_path(manifest: BuildManifest, visual_name: str) -> str:
    for part in manifest.parts:
        if part.name == visual_name:
            record = next(item for item in part.exports if item.format == "stl")
            return record.path
    for asset in manifest.assets:
        if asset.name == visual_name:
            stl_record = next(
                (item for item in asset.exports if item.format == "stl"), None
            )
            if stl_record is not None:
                return stl_record.path
            return asset.path
    for assembly in manifest.assemblies:
        if assembly.name == visual_name:
            record = next(item for item in assembly.exports if item.format == "glb")
            return record.path
    raise KeyError(f"Unable to resolve visual mesh path for {visual_name}")
