from __future__ import annotations

from embod.model.core import CollisionDef, PrintProfile, Project


def test_project_registries() -> None:
    project = Project("unit_test")
    project.interface(name="mount_face", kind="bolt_pattern")
    project.part(
        name="placeholder",
        geometry=object(),
        print_profile=PrintProfile(process="fdm", material="PLA"),
    )
    project.asset(name="asset", path="fixture.step", kind="step")
    robot = project.robot("robot")
    robot.link(name="base")
    assert "mount_face" in project.interfaces
    assert "placeholder" in project.parts
    assert "asset" in project.imported_assets
    assert "robot" in project.robots


def test_collision_factories() -> None:
    box = CollisionDef.box(1.0, 2.0, 3.0)
    cylinder = CollisionDef.cylinder(4.0, 5.0, axis="y")
    sphere = CollisionDef.sphere(6.0)
    assert box.size_mm == (1.0, 2.0, 3.0)
    assert cylinder.axis == "y"
    assert sphere.radius_mm == 6.0
