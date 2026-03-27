import cadquery as cq

from embod import AssemblyComponent, CollisionDef, PrintProfile, Project

project = Project("diff_drive_robot")
robot = project.robot("diff_drive_robot")

wheel = project.part(
    name="wheel",
    geometry=cq.Workplane().cylinder(20.0, 16.0),
    print_profile=PrintProfile(process="fdm", material="TPU"),
    tags=["printable", "wheel"],
)

body = project.part(
    name="body",
    geometry=cq.Workplane().box(120.0, 80.0, 18.0),
    print_profile=PrintProfile(process="fdm", material="PETG"),
    tags=["printable", "structural"],
)

project.assembly(
    name="robot_visual",
    components=[
        AssemblyComponent(name="body", ref="body"),
        AssemblyComponent(
            name="left_wheel", ref="wheel", translation_mm=(0.0, 48.0, -4.0)
        ),
        AssemblyComponent(
            name="right_wheel", ref="wheel", translation_mm=(0.0, -48.0, -4.0)
        ),
    ],
)

robot.link(
    name="base_link",
    parts=["body"],
    assemblies=["robot_visual"],
    collision=CollisionDef.box(120.0, 80.0, 18.0),
    inertial_proxy=CollisionDef.box(120.0, 80.0, 18.0),
    mass_kg=1.5,
)
robot.link(
    name="left_wheel_link",
    parts=["wheel"],
    collision=CollisionDef.cylinder(radius_mm=16.0, length_mm=20.0, axis="y"),
    mass_kg=0.2,
    tags=["wheel"],
)
robot.link(
    name="right_wheel_link",
    parts=["wheel"],
    collision=CollisionDef.cylinder(radius_mm=16.0, length_mm=20.0, axis="y"),
    mass_kg=0.2,
    tags=["wheel"],
)
robot.joint(
    name="left_joint",
    parent="base_link",
    child="left_wheel_link",
    joint_type="continuous",
    origin_xyz=(0.0, 48.0, -4.0),
    axis_xyz=(0.0, 1.0, 0.0),
)
robot.joint(
    name="right_joint",
    parent="base_link",
    child="right_wheel_link",
    joint_type="continuous",
    origin_xyz=(0.0, -48.0, -4.0),
    axis_xyz=(0.0, 1.0, 0.0),
)
