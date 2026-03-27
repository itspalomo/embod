from __future__ import annotations

from embod.model.core import CollisionDef, MeshProfile, PrintProfile, Project


def test_project_registries() -> None:
    project = Project("unit_test")
    mesh_profile = MeshProfile(tolerance_mm=0.03, angular_tolerance_rad=0.025)
    project.interface(name="mount_face", kind="bolt_pattern")
    project.part(
        name="placeholder",
        geometry=object(),
        print_profile=PrintProfile(process="fdm", material="PLA"),
        mesh_profile=mesh_profile,
    )
    project.asset(
        name="asset",
        path="fixture.step",
        kind="step",
        mesh_profile=mesh_profile,
    )
    robot = project.robot("robot")
    robot.link(name="base")
    assert "mount_face" in project.interfaces
    assert "placeholder" in project.parts
    assert "asset" in project.imported_assets
    assert "robot" in project.robots
    assert project.parts["placeholder"].mesh_profile == mesh_profile
    assert project.imported_assets["asset"].mesh_profile == mesh_profile


def test_collision_factories() -> None:
    box = CollisionDef.box(1.0, 2.0, 3.0)
    cylinder = CollisionDef.cylinder(4.0, 5.0, axis="y")
    sphere = CollisionDef.sphere(6.0)
    assert box.size_mm == (1.0, 2.0, 3.0)
    assert cylinder.axis == "y"
    assert sphere.radius_mm == 6.0


def test_mesh_profile_defaults() -> None:
    mesh_profile = MeshProfile()
    assert mesh_profile.tolerance_mm == 0.05
    assert mesh_profile.angular_tolerance_rad == 0.05
