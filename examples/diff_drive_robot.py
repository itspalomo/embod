import cadquery as cq

from embod import AssemblyComponent, CollisionDef, MeshProfile, PrintProfile, Project

project = Project("diff_drive_robot")
robot = project.robot("diff_drive_robot")

wheel = project.part(
    name="wheel",
    geometry=(
        cq.Workplane("XZ")
        .circle(32.0)
        .extrude(14.0, both=True)
        .faces(">Y")
        .workplane()
        .circle(24.0)
        .cutBlind(-6.0)
        .faces("<Y")
        .workplane()
        .circle(24.0)
        .cutBlind(-6.0)
        .faces(">Y")
        .workplane()
        .hole(8.0)
        .faces(">Y")
        .workplane()
        .pushPoints([(-14.0, 0.0), (14.0, 0.0), (0.0, 14.0), (0.0, -14.0)])
        .hole(10.0)
    ),
    mesh_profile=MeshProfile(tolerance_mm=0.02, angular_tolerance_rad=0.02),
    print_profile=PrintProfile(process="fdm", material="TPU"),
    tags=["printable", "wheel"],
)

body = project.part(
    name="body",
    geometry=(
        cq.Workplane("XY")
        .box(140.0, 88.0, 16.0)
        .edges("|Z")
        .fillet(10.0)
        .faces(">Z")
        .workplane()
        .rect(88.0, 52.0)
        .cutBlind(-8.0)
        .faces(">Z")
        .workplane()
        .pushPoints([(-46.0, -24.0), (-46.0, 24.0), (46.0, -24.0), (46.0, 24.0)])
        .circle(6.0)
        .extrude(12.0)
        .faces(">Z")
        .workplane(offset=12.0)
        .pushPoints([(-46.0, -24.0), (-46.0, 24.0), (46.0, -24.0), (46.0, 24.0)])
        .hole(3.2)
    ),
    mesh_profile=MeshProfile(tolerance_mm=0.04, angular_tolerance_rad=0.035),
    print_profile=PrintProfile(process="fdm", material="PETG"),
    tags=["printable", "structural"],
)

sensor_mast = project.part(
    name="sensor_mast",
    geometry=(
        cq.Workplane("XY")
        .box(18.0, 42.0, 54.0)
        .translate((0.0, 0.0, 27.0))
        .edges("|Z")
        .fillet(2.0)
        .faces(">Y")
        .workplane()
        .pushPoints([(0.0, 14.0), (0.0, 30.0)])
        .hole(4.0)
    ),
    mesh_profile=MeshProfile(tolerance_mm=0.03, angular_tolerance_rad=0.025),
    print_profile=PrintProfile(process="fdm", material="PETG"),
    tags=["printable", "sensor_mount"],
)

project.assembly(
    name="robot_visual",
    components=[
        AssemblyComponent(name="body", ref="body"),
        AssemblyComponent(
            name="left_wheel", ref="wheel", translation_mm=(0.0, 62.0, -24.0)
        ),
        AssemblyComponent(
            name="right_wheel", ref="wheel", translation_mm=(0.0, -62.0, -24.0)
        ),
        AssemblyComponent(
            name="sensor_mast", ref="sensor_mast", translation_mm=(36.0, 0.0, 8.0)
        ),
    ],
)

robot.link(
    name="base_link",
    parts=["body", "sensor_mast"],
    assemblies=["robot_visual"],
    collision=CollisionDef.box(140.0, 88.0, 28.0),
    inertial_proxy=CollisionDef.box(140.0, 88.0, 28.0),
    mass_kg=2.1,
)
robot.link(
    name="left_wheel_link",
    parts=["wheel"],
    collision=CollisionDef.cylinder(radius_mm=32.0, length_mm=28.0, axis="y"),
    mass_kg=0.35,
    tags=["wheel"],
)
robot.link(
    name="right_wheel_link",
    parts=["wheel"],
    collision=CollisionDef.cylinder(radius_mm=32.0, length_mm=28.0, axis="y"),
    mass_kg=0.35,
    tags=["wheel"],
)
robot.joint(
    name="left_joint",
    parent="base_link",
    child="left_wheel_link",
    joint_type="continuous",
    origin_xyz=(0.0, 62.0, -24.0),
    axis_xyz=(0.0, 1.0, 0.0),
)
robot.joint(
    name="right_joint",
    parent="base_link",
    child="right_wheel_link",
    joint_type="continuous",
    origin_xyz=(0.0, -62.0, -24.0),
    axis_xyz=(0.0, 1.0, 0.0),
)
robot.frame(
    name="front_camera_frame",
    parent="base_link",
    origin_xyz=(54.0, 0.0, 62.0),
)
robot.sensor(
    name="front_camera",
    kind="rgbd",
    frame="front_camera_frame",
    params={"hfov_deg": 92.0, "vfov_deg": 58.0},
)
