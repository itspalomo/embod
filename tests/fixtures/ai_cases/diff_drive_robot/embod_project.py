import cadquery as cq

from embod import AssemblyComponent, CollisionDef, PrintProfile, Project

project = Project("diff_drive_case")
robot = project.robot("diff_drive_case")

project.part(
    name="wheel",
    geometry=cq.Workplane().cylinder(22.0, 16.0),
    print_profile=PrintProfile(process="fdm", material="TPU"),
    tags=["printable", "wheel"],
)
project.part(
    name="chassis",
    geometry=cq.Workplane().box(90.0, 70.0, 18.0),
    print_profile=PrintProfile(process="fdm", material="PETG"),
    tags=["printable", "structural"],
)
project.assembly(
    name="robot_visual",
    components=[
        AssemblyComponent(name="chassis_instance", ref="chassis"),
        AssemblyComponent(
            name="left_wheel_instance", ref="wheel", translation_mm=(0.0, 42.0, -4.0)
        ),
        AssemblyComponent(
            name="right_wheel_instance", ref="wheel", translation_mm=(0.0, -42.0, -4.0)
        ),
    ],
)

robot.link(
    name="base_link",
    parts=["chassis"],
    assemblies=["robot_visual"],
    collision=CollisionDef.box(90.0, 70.0, 18.0),
    inertial_proxy=CollisionDef.box(90.0, 70.0, 18.0),
    mass_kg=1.1,
)
robot.link(
    name="left_wheel_link",
    parts=["wheel"],
    collision=CollisionDef.cylinder(radius_mm=16.0, length_mm=22.0, axis="y"),
    mass_kg=0.15,
    tags=["wheel"],
)
robot.link(
    name="right_wheel_link",
    parts=["wheel"],
    collision=CollisionDef.cylinder(radius_mm=16.0, length_mm=22.0, axis="y"),
    mass_kg=0.15,
    tags=["wheel"],
)
robot.joint(
    name="left_joint",
    parent="base_link",
    child="left_wheel_link",
    joint_type="continuous",
    origin_xyz=(0.0, 42.0, -4.0),
    axis_xyz=(0.0, 1.0, 0.0),
)
robot.joint(
    name="right_joint",
    parent="base_link",
    child="right_wheel_link",
    joint_type="continuous",
    origin_xyz=(0.0, -42.0, -4.0),
    axis_xyz=(0.0, 1.0, 0.0),
)
