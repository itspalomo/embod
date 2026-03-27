from __future__ import annotations

from pathlib import Path

import cadquery as cq

from embod.geometry_pipeline import (
    apply_brep_operations,
    brep_source_type,
    mesh_bounds_and_stats,
    mesh_operation_manifests,
    resolve_brep_geometry_source,
)
from embod.model.core import (
    Assembly as ProjectAssembly,
)
from embod.model.core import (
    AssemblyComponent,
    CollisionDef,
    ImportedAsset,
    MeshProfile,
    Part,
    Project,
)
from embod.model.manifest import (
    AssemblyComponentManifest,
    AssemblyManifest,
    AssetManifest,
    EntityBounds,
    ExportRecord,
    GeometryStats,
    PartManifest,
)
from embod.runtime import copy_file, ensure_dir

DEFAULT_MESH_PROFILE = MeshProfile()


def _shape_bounds(shape: cq.Shape) -> EntityBounds:
    bbox = shape.BoundingBox()
    return EntityBounds(x_mm=bbox.xlen, y_mm=bbox.ylen, z_mm=bbox.zlen)


def _shape_stats(shape: cq.Shape) -> GeometryStats:
    solids = shape.Solids()
    return GeometryStats(
        volume_mm3=shape.Volume(),
        is_solid=not shape.isNull() and len(solids) > 0,
        solid_count=len(solids),
    )


def _rotate_shape(
    workplane: cq.Workplane, component: AssemblyComponent
) -> cq.Workplane:
    rotated = workplane
    roll, pitch, yaw = component.rotation_rpy_deg
    if roll != 0:
        rotated = rotated.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), roll)
    if pitch != 0:
        rotated = rotated.rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), pitch)
    if yaw != 0:
        rotated = rotated.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), yaw)
    return rotated.translate(component.translation_mm)


def _color_from_name(color: str | None) -> cq.Color | None:
    return cq.Color(color) if color is not None else None


def _asset_workplane(asset: ImportedAsset, source_root: Path) -> cq.Workplane:
    absolute = (source_root / asset.path).resolve()
    if asset.kind == "step":
        return cq.importers.importStep(str(absolute))
    raise ValueError(f"Asset {asset.name} is not importable into CAD geometry")


def _effective_mesh_profile(profile: MeshProfile | None) -> MeshProfile:
    if profile is None:
        return DEFAULT_MESH_PROFILE
    return profile


def _mesh_profile_payload(profile: MeshProfile | None) -> dict[str, float]:
    effective = _effective_mesh_profile(profile)
    return {
        "tolerance_mm": effective.tolerance_mm,
        "angular_tolerance_rad": effective.angular_tolerance_rad,
    }


def export_part(
    part: Part,
    *,
    build_dir: Path,
    project: Project | None = None,
    source_root: Path | None = None,
) -> PartManifest:
    part_dir = ensure_dir(build_dir / "parts" / part.name)
    source = part.geometry_source
    if source is None:
        raise RuntimeError(f"Part {part.name} is missing a geometry source")
    profile_payload: (
        dict[str, str | float | bool | tuple[float, float, float] | None] | None
    )
    if part.print_profile is None:
        profile_payload = None
    else:
        profile_payload = {
            "process": part.print_profile.process,
            "material": part.print_profile.material,
            "layer_height_mm": part.print_profile.layer_height_mm,
            "nozzle_mm": part.print_profile.nozzle_mm,
            "orientation": part.print_profile.orientation,
            "support_strategy": part.print_profile.support_strategy,
            "max_build_volume_mm": part.print_profile.max_build_volume_mm,
            "split_if_needed": part.print_profile.split_if_needed,
        }
    if source.kind == "imported_stl":
        if project is None or source_root is None or source.asset_name is None:
            raise RuntimeError("Imported STL parts need project and source_root")
        asset = project.imported_assets[source.asset_name]
        source_path = (source_root / asset.path).resolve()
        target_path = part_dir / f"{part.name}.stl"
        copy_file(source_path, target_path)
        bounds, geometry_stats, is_manifold = mesh_bounds_and_stats(target_path)
        operations, edit_failures = mesh_operation_manifests(part)
        if not is_manifold:
            edit_failures.append("mesh.non_manifold_source")
        return PartManifest(
            name=part.name,
            tags=part.tags,
            interfaces=part.interfaces,
            material=part.material,
            notes=part.notes,
            bounds=bounds,
            geometry=geometry_stats,
            source_type=brep_source_type(source.kind),
            resolved_source_kind=source.kind,
            mesh_profile=_mesh_profile_payload(part.mesh_profile),
            print_profile=profile_payload,
            operations=operations,
            edit_failures=edit_failures,
            exports=[ExportRecord(format="stl", path=str(target_path))],
        )
    step_path = part_dir / f"{part.name}.step"
    stl_path = part_dir / f"{part.name}.stl"
    workplane = resolve_brep_geometry_source(
        source,
        project=project,
        source_root=source_root,
    )
    workplane, operations, edit_failures = apply_brep_operations(
        workplane,
        part,
        project=project if project is not None else Project("standalone"),
    )
    mesh_profile = _effective_mesh_profile(part.mesh_profile)
    workplane.export(str(step_path))
    workplane.export(
        str(stl_path),
        tolerance=mesh_profile.tolerance_mm,
        angularTolerance=mesh_profile.angular_tolerance_rad,
    )
    shape = workplane.val()
    return PartManifest(
        name=part.name,
        tags=part.tags,
        interfaces=part.interfaces,
        material=part.material,
        notes=part.notes,
        bounds=_shape_bounds(shape),
        geometry=_shape_stats(shape),
        source_type=brep_source_type(source.kind),
        resolved_source_kind=source.kind,
        mesh_profile=_mesh_profile_payload(part.mesh_profile),
        print_profile=profile_payload,
        operations=operations,
        edit_failures=edit_failures,
        exports=[
            ExportRecord(format="step", path=str(step_path)),
            ExportRecord(format="stl", path=str(stl_path)),
        ],
    )


def export_asset(
    asset: ImportedAsset,
    *,
    source_root: Path,
    build_dir: Path,
) -> AssetManifest:
    assets_dir = ensure_dir(build_dir / "assets" / asset.name)
    source_path = (source_root / asset.path).resolve()
    target_path = assets_dir / source_path.name
    exists = source_path.exists()
    bounds: EntityBounds | None = None
    mesh_profile: dict[str, float] | None = None
    exports: list[ExportRecord] = []
    if exists:
        copy_file(source_path, target_path)
        exports.append(ExportRecord(format=asset.kind, path=str(target_path)))
        if asset.kind == "step":
            workplane = cq.importers.importStep(str(source_path))
            stl_path = assets_dir / f"{asset.name}.stl"
            effective_mesh_profile = _effective_mesh_profile(asset.mesh_profile)
            workplane.export(
                str(stl_path),
                tolerance=effective_mesh_profile.tolerance_mm,
                angularTolerance=effective_mesh_profile.angular_tolerance_rad,
            )
            exports.append(ExportRecord(format="stl", path=str(stl_path)))
            bounds = _shape_bounds(workplane.val())
            mesh_profile = _mesh_profile_payload(asset.mesh_profile)
        elif asset.kind == "stl":
            bounds, _, _ = mesh_bounds_and_stats(source_path)
    return AssetManifest(
        name=asset.name,
        kind=asset.kind,
        source_kind=f"imported_{asset.kind}",
        path=str(source_path),
        tags=asset.tags,
        printable=asset.printable,
        exists=exists,
        bounds=bounds,
        mesh_profile=mesh_profile,
        exports=exports,
    )


def _build_component_geometry(
    component: AssemblyComponent,
    *,
    project: Project,
    source_root: Path,
) -> tuple[cq.Assembly | cq.Workplane, EntityBounds | None]:
    if component.ref in project.parts:
        part = project.parts[component.ref]
        if not isinstance(part.geometry, cq.Workplane):
            raise TypeError(f"Part {part.name} geometry must be a cadquery.Workplane")
        geometry = _rotate_shape(part.geometry, component)
        return geometry, _shape_bounds(geometry.val())
    if component.ref in project.imported_assets:
        workplane = _asset_workplane(
            project.imported_assets[component.ref], source_root
        )
        geometry = _rotate_shape(workplane, component)
        return geometry, _shape_bounds(geometry.val())
    if component.ref in project.assemblies:
        nested = build_assembly(
            project.assemblies[component.ref],
            project=project,
            source_root=source_root,
        )
        return nested[0], nested[1]
    raise KeyError(f"Unknown assembly component reference {component.ref}")


def build_assembly(
    assembly: ProjectAssembly,
    *,
    project: Project,
    source_root: Path,
) -> tuple[cq.Assembly, EntityBounds | None]:
    cq_assembly = cq.Assembly(name=assembly.name)
    bounds: EntityBounds | None = None
    for component in assembly.components:
        built_geometry, built_bounds = _build_component_geometry(
            component,
            project=project,
            source_root=source_root,
        )
        if isinstance(built_geometry, cq.Assembly):
            cq_assembly.add(
                built_geometry,
                name=component.name,
                color=_color_from_name(component.color),
            )
        else:
            cq_assembly.add(
                built_geometry,
                name=component.name,
                color=_color_from_name(component.color),
            )
        if built_bounds is not None:
            if bounds is None:
                bounds = built_bounds
            else:
                bounds = EntityBounds(
                    x_mm=max(bounds.x_mm, built_bounds.x_mm),
                    y_mm=max(bounds.y_mm, built_bounds.y_mm),
                    z_mm=max(bounds.z_mm, built_bounds.z_mm),
                )
    return cq_assembly, bounds


def export_assembly(
    assembly: ProjectAssembly,
    *,
    project: Project,
    source_root: Path,
    build_dir: Path,
) -> AssemblyManifest:
    assembly_dir = ensure_dir(build_dir / "assemblies" / assembly.name)
    built_assembly, built_bounds = build_assembly(
        assembly,
        project=project,
        source_root=source_root,
    )
    step_path = assembly_dir / f"{assembly.name}.step"
    glb_path = assembly_dir / f"{assembly.name}.glb"
    built_assembly.export(str(step_path))
    built_assembly.export(str(glb_path))
    return AssemblyManifest(
        name=assembly.name,
        tags=assembly.tags,
        components=[
            AssemblyComponentManifest(
                name=component.name,
                ref=component.ref,
                translation_mm=component.translation_mm,
                rotation_rpy_deg=component.rotation_rpy_deg,
                color=component.color,
            )
            for component in assembly.components
        ],
        bounds=built_bounds,
        exports=[
            ExportRecord(format="step", path=str(step_path)),
            ExportRecord(format="glb", path=str(glb_path)),
        ],
    )


def collision_bounds(collision: CollisionDef) -> EntityBounds | None:
    if collision.kind == "box" and collision.size_mm is not None:
        x_mm, y_mm, z_mm = collision.size_mm
        return EntityBounds(x_mm=x_mm, y_mm=y_mm, z_mm=z_mm)
    if (
        collision.kind == "cylinder"
        and collision.radius_mm is not None
        and collision.length_mm is not None
    ):
        diameter = collision.radius_mm * 2.0
        if collision.axis == "x":
            return EntityBounds(x_mm=collision.length_mm, y_mm=diameter, z_mm=diameter)
        if collision.axis == "y":
            return EntityBounds(x_mm=diameter, y_mm=collision.length_mm, z_mm=diameter)
        return EntityBounds(x_mm=diameter, y_mm=diameter, z_mm=collision.length_mm)
    if collision.kind == "sphere" and collision.radius_mm is not None:
        diameter = collision.radius_mm * 2.0
        return EntityBounds(x_mm=diameter, y_mm=diameter, z_mm=diameter)
    return None
