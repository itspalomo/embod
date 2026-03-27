from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

import cadquery as cq

from embod.model.core import (
    BooleanOp,
    FeaturePlacement,
    GeometryOperation,
    GeometrySource,
    Part,
    PrintProfile,
    Project,
    SupportOp,
    TextOp,
    Vector3,
)
from embod.model.manifest import (
    EntityBounds,
    GeometryStats,
    OperationManifest,
    PlacementCandidateManifest,
    PlacementDecisionManifest,
)

VALID_SURFACE_SELECTORS = (">Z", "<Z", ">Y", "<Y", ">X", "<X")
AUTO_SELECTOR_ORDER = (">Z", "<Z", ">Y", "<Y", ">X", "<X")
PLACEMENT_EPSILON_MM = 0.05


@dataclass(slots=True, frozen=True)
class PlacementResolution:
    decision: PlacementDecisionManifest | None
    candidates: list[PlacementCandidateManifest]
    warnings: list[str]
    failures: list[str]


def default_text_font_path() -> Path:
    return Path(str(files("embod.assets").joinpath("DejaVuSans.ttf")))


def brep_source_type(source_kind: str) -> str:
    if source_kind == "native_cadquery":
        return "cadquery"
    if source_kind == "imported_step":
        return "step_asset"
    if source_kind == "imported_stl":
        return "mesh"
    return source_kind


def resolve_brep_geometry_source(
    source: GeometrySource,
    *,
    project: Project | None,
    source_root: Path | None,
) -> cq.Workplane:
    if source.kind == "native_cadquery":
        if not isinstance(source.geometry, cq.Workplane):
            raise TypeError("Native geometry sources must be cadquery.Workplane")
        return source.geometry
    if source.kind != "imported_step":
        raise TypeError(f"Geometry source {source.kind} is not a BRep source")
    if project is None or source_root is None or source.asset_name is None:
        raise RuntimeError("Imported STEP sources need project and source_root")
    asset = project.imported_assets[source.asset_name]
    if asset.kind != "step":
        raise TypeError(
            f"Geometry source {source.asset_name} must reference a STEP asset"
        )
    return cq.importers.importStep(str((source_root / asset.path).resolve()))


def mesh_bounds_and_stats(mesh_path: Path) -> tuple[EntityBounds, GeometryStats, bool]:
    import pyvista as pv

    mesh = pv.read(str(mesh_path))
    bounds = mesh.bounds
    volume = float(mesh.volume)
    is_manifold = bool(mesh.is_manifold)
    entity_bounds = EntityBounds(
        x_mm=float(bounds[1] - bounds[0]),
        y_mm=float(bounds[3] - bounds[2]),
        z_mm=float(bounds[5] - bounds[4]),
    )
    return (
        entity_bounds,
        GeometryStats(
            volume_mm3=volume,
            is_solid=volume > 0.0 and is_manifold,
            solid_count=1 if volume > 0.0 else 0,
        ),
        is_manifold,
    )


def apply_brep_operations(
    workplane: cq.Workplane,
    part: Part,
    *,
    project: Project,
) -> tuple[cq.Workplane, list[OperationManifest], list[str]]:
    current = workplane
    manifests: list[OperationManifest] = []
    edit_failures: list[str] = []
    for operation in part.operations:
        tool = _build_brep_tool(operation)
        if tool is None:
            manifest = OperationManifest(
                name=_operation_name(operation),
                kind=_operation_kind(operation),
                summary=_operation_summary(operation),
                status="failed",
                edit_failures=["geometry.unsupported_operation_tool"],
            )
            manifests.append(manifest)
            edit_failures.extend(manifest.edit_failures)
            continue
        shape = current.val()
        resolution = _resolve_placement(
            part=part,
            operation=operation,
            project=project,
            bounds=_shape_bounds(shape),
            tool_bounds=_shape_bounds(tool.val()),
        )
        if resolution.decision is None:
            manifest = OperationManifest(
                name=_operation_name(operation),
                kind=_operation_kind(operation),
                summary=_operation_summary(operation),
                status="failed",
                warnings=resolution.warnings,
                edit_failures=resolution.failures,
                placement_candidates=resolution.candidates,
            )
            manifests.append(manifest)
            edit_failures.extend(resolution.failures)
            continue
        try:
            current = _apply_operation(
                current=current,
                operation=operation,
                tool=tool,
                decision=resolution.decision,
                part_bounds=_shape_bounds(current.val()),
            )
            status = "applied"
        except ValueError as exc:
            status = "failed"
            resolution = PlacementResolution(
                decision=resolution.decision,
                candidates=resolution.candidates,
                warnings=resolution.warnings,
                failures=[f"geometry.{exc!s}"],
            )
            edit_failures.extend(resolution.failures)
        manifests.append(
            OperationManifest(
                name=_operation_name(operation),
                kind=_operation_kind(operation),
                summary=_operation_summary(operation),
                status=status,
                warnings=resolution.warnings,
                edit_failures=resolution.failures,
                selected_placement=resolution.decision,
                placement_candidates=resolution.candidates,
            )
        )
    return current, manifests, edit_failures


def mesh_operation_manifests(part: Part) -> tuple[list[OperationManifest], list[str]]:
    failures: list[str] = []
    manifests: list[OperationManifest] = []
    for operation in part.operations:
        manifest = OperationManifest(
            name=_operation_name(operation),
            kind=_operation_kind(operation),
            summary=_operation_summary(operation),
            status="failed",
            edit_failures=["mesh.phase_gated_stl_mods"],
        )
        manifests.append(manifest)
        failures.extend(manifest.edit_failures)
    return manifests, failures


def _build_brep_tool(operation: GeometryOperation) -> cq.Workplane | None:
    if isinstance(operation, TextOp):
        font_path = operation.font_path or str(default_text_font_path())
        return cq.Workplane("XY").text(
            operation.text,
            operation.font_size_mm,
            operation.depth_mm,
            combine=False,
            fontPath=font_path,
            halign=operation.halign,
            valign=operation.valign,
        )
    if isinstance(operation, BooleanOp):
        return operation.tool if isinstance(operation.tool, cq.Workplane) else None
    if isinstance(operation, SupportOp):
        tool = cq.Workplane("XY").box(
            operation.width_mm, operation.height_mm, operation.thickness_mm
        )
        hole_diameter = operation.hole_diameter_mm
        hole_spacing = operation.hole_spacing_mm
        if hole_diameter is not None:
            points = [(0.0, 0.0)]
            if hole_spacing is not None and hole_spacing > 0.0:
                points = [(-hole_spacing / 2.0, 0.0), (hole_spacing / 2.0, 0.0)]
            tool = tool.faces(">Z").workplane().pushPoints(points).hole(hole_diameter)
        return tool
    return None


def _apply_operation(
    *,
    current: cq.Workplane,
    operation: GeometryOperation,
    tool: cq.Workplane,
    decision: PlacementDecisionManifest,
    part_bounds: EntityBounds,
) -> cq.Workplane:
    selector = decision.selector
    if selector not in VALID_SURFACE_SELECTORS:
        raise ValueError("invalid_surface_selector")
    effective_depth = _effective_tool_depth(operation, part_bounds, decision)
    outward_offset = _placement_offset_mm(operation, effective_depth)
    placed = _rotate_workplane(tool, decision.origin_rpy_deg)
    normal = _selector_normal(selector)
    origin = _vector_add(
        decision.origin_xyz_mm,
        (
            normal[0] * outward_offset,
            normal[1] * outward_offset,
            normal[2] * outward_offset,
        ),
    )
    placed = placed.translate(origin)
    if _is_additive(operation):
        return current.union(placed)
    return current.cut(placed)


def _resolve_placement(
    *,
    part: Part,
    operation: GeometryOperation,
    project: Project,
    bounds: EntityBounds,
    tool_bounds: EntityBounds,
) -> PlacementResolution:
    placement = _operation_placement(operation)
    if placement.interface is not None:
        return _resolve_interface_placement(
            part=part,
            operation=operation,
            project=project,
            interface_name=placement.interface,
            bounds=bounds,
            tool_bounds=tool_bounds,
        )
    if placement.surface_selector is not None:
        return _resolve_explicit_surface_placement(
            operation=operation,
            bounds=bounds,
            tool_bounds=tool_bounds,
            selector=placement.surface_selector,
            placement=placement,
        )
    return _resolve_auto_placement(
        operation=operation,
        bounds=bounds,
        tool_bounds=tool_bounds,
        print_profile=part.print_profile,
    )


def _resolve_interface_placement(
    *,
    part: Part,
    operation: GeometryOperation,
    project: Project,
    interface_name: str,
    bounds: EntityBounds,
    tool_bounds: EntityBounds,
) -> PlacementResolution:
    interface = project.interfaces.get(interface_name)
    if interface is None:
        return PlacementResolution(
            decision=None,
            candidates=[],
            warnings=[],
            failures=["placement.missing_interface"],
        )
    allowed = interface.allowed_operation_kinds
    operation_kind = _operation_kind(operation)
    if allowed and operation_kind not in allowed:
        return PlacementResolution(
            decision=None,
            candidates=[],
            warnings=[],
            failures=["placement.operation_not_allowed"],
        )
    source = part.geometry_source
    asset_name = source.asset_name if source is not None else None
    if interface.target is not None and interface.target not in {part.name, asset_name}:
        return PlacementResolution(
            decision=None,
            candidates=[],
            warnings=[],
            failures=["placement.interface_target_mismatch"],
        )
    selector = (
        interface.surface_selector
        or _operation_placement(operation).surface_selector
    )
    if selector is None:
        selector = ">Z"
    candidate = _candidate_for_selector(bounds, selector, part.print_profile)
    if candidate is None:
        return PlacementResolution(
            decision=None,
            candidates=[],
            warnings=[],
            failures=["placement.curved_only_surface"],
        )
    failures = _check_candidate_constraints(
        candidate=candidate,
        operation=operation,
        tool_bounds=tool_bounds,
        thickness_mm=_selector_thickness(bounds, selector),
        clearance_mm=_effective_clearance(
            _operation_placement(operation), interface.clearance_mm
        ),
    )
    if failures:
        return PlacementResolution(
            decision=None,
            candidates=[candidate],
            warnings=[],
            failures=failures,
        )
    decision = PlacementDecisionManifest(
        strategy="interface",
        selector=selector,
        score=candidate.score,
        origin_xyz_mm=_vector_add(
            interface.origin_xyz_mm, _operation_placement(operation).offset_mm
        ),
        origin_rpy_deg=_vector_add(
            _vector_add(candidate.origin_rpy_deg, interface.origin_rpy_deg),
            _operation_placement(operation).rotation_rpy_deg,
        ),
        interface=interface.name,
    )
    return PlacementResolution(
        decision=decision,
        candidates=[
            PlacementCandidateManifest(
                strategy="interface",
                selector=selector,
                score=candidate.score,
                origin_xyz_mm=decision.origin_xyz_mm,
                origin_rpy_deg=decision.origin_rpy_deg,
                score_breakdown=candidate.score_breakdown,
                warnings=[],
                interface=interface.name,
            )
        ],
        warnings=[],
        failures=[],
    )


def _resolve_explicit_surface_placement(
    *,
    operation: GeometryOperation,
    bounds: EntityBounds,
    tool_bounds: EntityBounds,
    selector: str,
    placement: FeaturePlacement,
) -> PlacementResolution:
    candidate = _candidate_for_selector(bounds, selector, None)
    if candidate is None:
        return PlacementResolution(
            decision=None,
            candidates=[],
            warnings=[],
            failures=["placement.curved_only_surface"],
        )
    failures = _check_candidate_constraints(
        candidate=candidate,
        operation=operation,
        tool_bounds=tool_bounds,
        thickness_mm=_selector_thickness(bounds, selector),
        clearance_mm=_effective_clearance(placement, None),
    )
    if failures:
        return PlacementResolution(
            decision=None,
            candidates=[candidate],
            warnings=[],
            failures=failures,
        )
    decision = PlacementDecisionManifest(
        strategy="surface_selector",
        selector=selector,
        score=candidate.score,
        origin_xyz_mm=_vector_add(candidate.origin_xyz_mm, placement.offset_mm),
        origin_rpy_deg=_vector_add(
            candidate.origin_rpy_deg, placement.rotation_rpy_deg
        ),
    )
    return PlacementResolution(
        decision=decision,
        candidates=[
            PlacementCandidateManifest(
                strategy="surface_selector",
                selector=selector,
                score=candidate.score,
                origin_xyz_mm=decision.origin_xyz_mm,
                origin_rpy_deg=decision.origin_rpy_deg,
                score_breakdown=candidate.score_breakdown,
                warnings=[],
            )
        ],
        warnings=[],
        failures=[],
    )


def _resolve_auto_placement(
    *,
    operation: GeometryOperation,
    bounds: EntityBounds,
    tool_bounds: EntityBounds,
    print_profile: PrintProfile | None,
) -> PlacementResolution:
    clearance = _effective_clearance(_operation_placement(operation), None)
    ranked = [
        candidate
        for selector in AUTO_SELECTOR_ORDER
        if (
            candidate := _candidate_for_selector(bounds, selector, print_profile)
        )
        is not None
    ]
    valid: list[PlacementCandidateManifest] = []
    for candidate in ranked:
        failures = _check_candidate_constraints(
            candidate=candidate,
            operation=operation,
            tool_bounds=tool_bounds,
            thickness_mm=_selector_thickness(bounds, candidate.selector),
            clearance_mm=clearance,
        )
        if not failures:
            valid.append(candidate)
    if not valid:
        return PlacementResolution(
            decision=None,
            candidates=ranked,
            warnings=[],
            failures=["placement.no_valid_target_surface"],
        )
    sorted_candidates = sorted(valid, key=lambda item: (-item.score, item.selector))
    chosen = sorted_candidates[0]
    warnings: list[str] = []
    if (
        len(sorted_candidates) > 1
        and abs(sorted_candidates[0].score - sorted_candidates[1].score) < 0.03
    ):
        warnings.append("placement.ambiguous_best_surface")
    decision = PlacementDecisionManifest(
        strategy="auto",
        selector=chosen.selector,
        score=chosen.score,
        origin_xyz_mm=_vector_add(
            chosen.origin_xyz_mm, _operation_placement(operation).offset_mm
        ),
        origin_rpy_deg=_vector_add(
            chosen.origin_rpy_deg, _operation_placement(operation).rotation_rpy_deg
        ),
    )
    return PlacementResolution(
        decision=decision,
        candidates=sorted_candidates,
        warnings=warnings,
        failures=[],
    )


def _candidate_for_selector(
    bounds: EntityBounds, selector: str, print_profile: PrintProfile | None
) -> PlacementCandidateManifest | None:
    if selector not in VALID_SURFACE_SELECTORS:
        return None
    center = (0.0, 0.0, 0.0)
    x_half = bounds.x_mm / 2.0
    y_half = bounds.y_mm / 2.0
    z_half = bounds.z_mm / 2.0
    plane_x: float
    plane_y: float
    thickness: float
    origin: Vector3
    rpy: Vector3
    if selector == ">Z":
        plane_x, plane_y, thickness = bounds.x_mm, bounds.y_mm, bounds.z_mm
        origin = (center[0], center[1], z_half)
        rpy = (0.0, 0.0, 0.0)
    elif selector == "<Z":
        plane_x, plane_y, thickness = bounds.x_mm, bounds.y_mm, bounds.z_mm
        origin = (center[0], center[1], -z_half)
        rpy = (180.0, 0.0, 0.0)
    elif selector == ">Y":
        plane_x, plane_y, thickness = bounds.x_mm, bounds.z_mm, bounds.y_mm
        origin = (center[0], y_half, center[2])
        rpy = (-90.0, 0.0, 0.0)
    elif selector == "<Y":
        plane_x, plane_y, thickness = bounds.x_mm, bounds.z_mm, bounds.y_mm
        origin = (center[0], -y_half, center[2])
        rpy = (90.0, 0.0, 0.0)
    elif selector == ">X":
        plane_x, plane_y, thickness = bounds.y_mm, bounds.z_mm, bounds.x_mm
        origin = (x_half, center[1], center[2])
        rpy = (0.0, 90.0, 0.0)
    else:
        plane_x, plane_y, thickness = bounds.y_mm, bounds.z_mm, bounds.x_mm
        origin = (-x_half, center[1], center[2])
        rpy = (0.0, -90.0, 0.0)
    area = plane_x * plane_y
    largest_area = max(
        bounds.x_mm * bounds.y_mm,
        bounds.x_mm * bounds.z_mm,
        bounds.y_mm * bounds.z_mm,
    )
    largest_axis = max(bounds.x_mm, bounds.y_mm, bounds.z_mm)
    area_score = area / largest_area if largest_area > 0.0 else 0.0
    clearance_score = (
        min(plane_x, plane_y) / largest_axis if largest_axis > 0.0 else 0.0
    )
    thickness_score = thickness / largest_axis if largest_axis > 0.0 else 0.0
    orientation_penalty = _orientation_penalty(selector, print_profile)
    support_penalty = _support_penalty(selector, print_profile)
    score_breakdown = {
        "flatness": 1.0,
        "usable_area": area_score,
        "edge_clearance": clearance_score,
        "local_thickness": thickness_score,
        "curvature_penalty": 0.0,
        "orientation_penalty": orientation_penalty,
        "support_penalty": support_penalty,
        "plane_x_mm": plane_x,
        "plane_y_mm": plane_y,
        "thickness_mm": thickness,
    }
    score = (
        0.40 * score_breakdown["usable_area"]
        + 0.20 * score_breakdown["edge_clearance"]
        + 0.20 * score_breakdown["local_thickness"]
        + 0.20 * score_breakdown["flatness"]
        - orientation_penalty
        - support_penalty
    )
    return PlacementCandidateManifest(
        strategy="auto",
        selector=selector,
        score=round(score, 6),
        origin_xyz_mm=origin,
        origin_rpy_deg=rpy,
        score_breakdown=score_breakdown,
    )


def _check_candidate_constraints(
    *,
    candidate: PlacementCandidateManifest,
    operation: GeometryOperation,
    tool_bounds: EntityBounds,
    thickness_mm: float,
    clearance_mm: float,
) -> list[str]:
    plane_x, plane_y = _selector_plane_size(candidate.selector, candidate, thickness_mm)
    available_x = plane_x - (2.0 * clearance_mm)
    available_y = plane_y - (2.0 * clearance_mm)
    if tool_bounds.x_mm > available_x or tool_bounds.y_mm > available_y:
        return ["placement.insufficient_clearance"]
    if _requires_embedded_depth(operation) and tool_bounds.z_mm >= max(
        thickness_mm - clearance_mm, 0.0
    ):
        return ["placement.insufficient_thickness"]
    return []


def _selector_plane_size(
    selector: str, candidate: PlacementCandidateManifest, thickness_mm: float
) -> tuple[float, float]:
    del selector, thickness_mm
    return (
        candidate.score_breakdown["plane_x_mm"],
        candidate.score_breakdown["plane_y_mm"],
    )


def _orientation_penalty(
    selector: str, print_profile: PrintProfile | None
) -> float:
    if print_profile is None or print_profile.orientation != "flat":
        return 0.0
    if selector == ">Z":
        return 0.0
    if selector == "<Z":
        return 0.08
    return 0.14


def _support_penalty(selector: str, print_profile: PrintProfile | None) -> float:
    if print_profile is None or print_profile.support_strategy is None:
        return 0.0
    if (
        print_profile.support_strategy.lower() in {"avoid", "minimal"}
        and selector != ">Z"
    ):
        return 0.10
    return 0.0


def _selector_thickness(bounds: EntityBounds, selector: str) -> float:
    if selector in {">Z", "<Z"}:
        return bounds.z_mm
    if selector in {">Y", "<Y"}:
        return bounds.y_mm
    return bounds.x_mm


def _effective_clearance(
    placement: FeaturePlacement, interface_clearance_mm: float | None
) -> float:
    if placement.min_clearance_mm is not None:
        return placement.min_clearance_mm
    if interface_clearance_mm is not None:
        return interface_clearance_mm
    return 1.0


def _effective_tool_depth(
    operation: GeometryOperation,
    part_bounds: EntityBounds,
    decision: PlacementDecisionManifest,
) -> float:
    if isinstance(operation, TextOp) and operation.mode == "cutout":
        return _selector_thickness(part_bounds, decision.selector) + 0.5
    return _tool_depth(operation)


def _tool_depth(operation: GeometryOperation) -> float:
    if isinstance(operation, TextOp):
        return operation.depth_mm
    if isinstance(operation, SupportOp):
        return operation.thickness_mm
    if isinstance(operation, BooleanOp) and isinstance(operation.tool, cq.Workplane):
        return _shape_bounds(operation.tool.val()).z_mm
    return 0.0


def _placement_offset_mm(operation: GeometryOperation, depth_mm: float) -> float:
    if _is_additive(operation):
        return (depth_mm / 2.0) - PLACEMENT_EPSILON_MM
    return -((depth_mm / 2.0) - PLACEMENT_EPSILON_MM)


def _requires_embedded_depth(operation: GeometryOperation) -> bool:
    return (isinstance(operation, TextOp) and operation.mode == "engrave") or (
        isinstance(operation, BooleanOp) and operation.mode == "cut"
    )


def _is_additive(operation: GeometryOperation) -> bool:
    if isinstance(operation, TextOp):
        return operation.mode == "emboss"
    if isinstance(operation, BooleanOp):
        return operation.mode == "add"
    return True


def _operation_name(operation: GeometryOperation) -> str:
    if isinstance(operation, TextOp):
        return operation.name
    if isinstance(operation, BooleanOp):
        return operation.name
    return operation.name


def _operation_kind(operation: GeometryOperation) -> str:
    if isinstance(operation, TextOp):
        return "text"
    if isinstance(operation, BooleanOp):
        return "boolean"
    return "support"


def _operation_summary(operation: GeometryOperation) -> str:
    if isinstance(operation, TextOp):
        return f"{operation.mode} text '{operation.text}'"
    if isinstance(operation, BooleanOp):
        return f"{operation.mode} boolean"
    return f"{operation.style} support"


def _operation_placement(operation: GeometryOperation) -> FeaturePlacement:
    if isinstance(operation, TextOp):
        return operation.placement
    if isinstance(operation, BooleanOp):
        return operation.placement
    return operation.placement


def _rotate_workplane(workplane: cq.Workplane, rpy_deg: Vector3) -> cq.Workplane:
    rotated = workplane
    roll, pitch, yaw = rpy_deg
    if roll != 0.0:
        rotated = rotated.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), roll)
    if pitch != 0.0:
        rotated = rotated.rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), pitch)
    if yaw != 0.0:
        rotated = rotated.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), yaw)
    return rotated


def _shape_bounds(shape: cq.Shape) -> EntityBounds:
    bbox = shape.BoundingBox()
    return EntityBounds(x_mm=bbox.xlen, y_mm=bbox.ylen, z_mm=bbox.zlen)


def _selector_normal(selector: str) -> Vector3:
    mapping: dict[str, Vector3] = {
        ">Z": (0.0, 0.0, 1.0),
        "<Z": (0.0, 0.0, -1.0),
        ">Y": (0.0, 1.0, 0.0),
        "<Y": (0.0, -1.0, 0.0),
        ">X": (1.0, 0.0, 0.0),
        "<X": (-1.0, 0.0, 0.0),
    }
    return mapping[selector]


def _vector_add(left: Vector3, right: Vector3) -> Vector3:
    return (left[0] + right[0], left[1] + right[1], left[2] + right[2])
