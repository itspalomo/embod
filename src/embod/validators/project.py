from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from embod.model.diagnostics import Diagnostic, DiagnosticLevel, DiagnosticsReport
from embod.model.manifest import (
    BuildManifest,
    CollisionManifest,
    EntityBounds,
    PrintabilityWarning,
    PrintReport,
)


def _warn(code: str, message: str, subject: str) -> Diagnostic:
    return Diagnostic(
        code=code, level=DiagnosticLevel.WARNING, message=message, subject=subject
    )


def _error(code: str, message: str, subject: str) -> Diagnostic:
    return Diagnostic(
        code=code, level=DiagnosticLevel.ERROR, message=message, subject=subject
    )


def _link_names(manifest: BuildManifest) -> set[str]:
    result: set[str] = set()
    for robot in manifest.robots:
        result.update(link.name for link in robot.links)
    return result


def _validate_collision(
    collision: CollisionManifest | None, subject: str
) -> Iterable[Diagnostic]:
    if collision is None:
        return []
    issues: list[Diagnostic] = []
    if collision.kind == "box" and collision.size_mm is None:
        issues.append(
            _error("robot.invalid_collision_box", "Box collisions need size", subject)
        )
    if collision.kind == "cylinder" and (
        collision.radius_mm is None or collision.length_mm is None
    ):
        issues.append(
            _error(
                "robot.invalid_collision_cylinder",
                "Cylinder collisions need radius and length",
                subject,
            )
        )
    return issues


def _validate_print_bounds(bounds: EntityBounds, subject: str) -> list[Diagnostic]:
    issues: list[Diagnostic] = []
    largest = max(bounds.x_mm, bounds.y_mm, bounds.z_mm)
    smallest = min(bounds.x_mm, bounds.y_mm, bounds.z_mm)
    if largest > 256.0:
        issues.append(
            _warning_or_error(
                largest > 300.0,
                "print.oversized_part",
                "Part exceeds a typical desktop build volume",
                subject,
            )
        )
    if smallest < 1.0:
        issues.append(
            _warn(
                "print.thin_axis",
                "Part has an axis under 1mm and may be fragile or unprintable",
                subject,
            )
        )
    return issues


def _warning_or_error(
    is_error: bool, code: str, message: str, subject: str
) -> Diagnostic:
    if is_error:
        return _error(code, message, subject)
    return _warn(code, message, subject)


def validate_manifest(manifest: BuildManifest) -> DiagnosticsReport:
    diagnostics: list[Diagnostic] = []
    seen: defaultdict[str, set[str]] = defaultdict(set)
    for part in manifest.parts:
        if part.name in seen["part"]:
            diagnostics.append(
                _error("geometry.duplicate_part", "Duplicate part name", part.name)
            )
        seen["part"].add(part.name)
        if not part.geometry.is_solid:
            diagnostics.append(
                _error(
                    "geometry.non_solid_part", "Part geometry is not solid", part.name
                )
            )
        diagnostics.extend(_validate_print_bounds(part.bounds, part.name))
        if "printable" in part.tags and part.print_profile is None:
            diagnostics.append(
                _warn(
                    "print.missing_profile",
                    "Printable part is missing a print profile",
                    part.name,
                )
            )
    for asset in manifest.assets:
        if not asset.exists:
            diagnostics.append(
                _error(
                    "geometry.missing_asset",
                    "Referenced asset file does not exist",
                    asset.name,
                )
            )
    links = _link_names(manifest)
    for robot in manifest.robots:
        child_names = {joint.child for joint in robot.joints}
        parent_names = {joint.parent for joint in robot.joints}
        roots = {link.name for link in robot.links} - child_names
        if len(roots) != 1:
            diagnostics.append(
                _error(
                    "graph.invalid_robot_roots",
                    "Robot must resolve to exactly one root link",
                    robot.name,
                )
            )
        for link in robot.links:
            diagnostics.extend(_validate_collision(link.collision, link.name))
            if link.mass_kg is None:
                diagnostics.append(
                    _warn("robot.missing_mass", "Link is missing mass", link.name)
                )
            if link.collision is None and link.name in parent_names.union(child_names):
                diagnostics.append(
                    _warn(
                        "robot.missing_collision",
                        "Movable or connected link is missing collision geometry",
                        link.name,
                    )
                )
            for part_name in link.parts:
                if part_name not in {
                    item.name for item in manifest.parts
                } and part_name not in {item.name for item in manifest.assets}:
                    diagnostics.append(
                        _error(
                            "graph.missing_link_part",
                            "Link references a missing part or asset",
                            link.name,
                        )
                    )
            if "wheel" in link.tags and link.collision is not None:
                diagnostics.extend(_validate_wheel_ground(link.collision, link.name))
        for joint in robot.joints:
            if joint.parent not in links:
                diagnostics.append(
                    _error(
                        "graph.missing_joint_parent",
                        "Joint parent link is missing",
                        joint.name,
                    )
                )
            if joint.child not in links:
                diagnostics.append(
                    _error(
                        "graph.missing_joint_child",
                        "Joint child link is missing",
                        joint.name,
                    )
                )
        for frame in robot.frames:
            if frame.parent not in links and frame.parent not in {
                item.name for item in robot.frames
            }:
                diagnostics.append(
                    _error(
                        "graph.missing_frame_parent",
                        "Frame parent is missing",
                        frame.name,
                    )
                )
        for sensor in robot.sensors:
            if sensor.frame not in {item.name for item in robot.frames}:
                diagnostics.append(
                    _error(
                        "graph.missing_sensor_frame",
                        "Sensor frame is missing",
                        sensor.name,
                    )
                )
    return DiagnosticsReport(diagnostics=diagnostics)


def _validate_wheel_ground(
    collision: CollisionManifest, subject: str
) -> Iterable[Diagnostic]:
    if collision.kind != "cylinder" or collision.radius_mm is None:
        return []
    if collision.origin_xyz_mm[2] > collision.radius_mm * 1.5:
        return [
            _warn(
                "robot.wheel_not_touching_ground",
                "Wheel center is far above expected ground contact",
                subject,
            )
        ]
    return []


def print_report(manifest: BuildManifest) -> PrintReport:
    warnings: list[PrintabilityWarning] = []
    report = validate_manifest(manifest)
    for diagnostic in report.diagnostics:
        if diagnostic.code.startswith("print."):
            warnings.append(
                PrintabilityWarning(
                    code=diagnostic.code,
                    subject=diagnostic.subject or "unknown",
                    message=diagnostic.message,
                )
            )
    return PrintReport(warnings=warnings)
