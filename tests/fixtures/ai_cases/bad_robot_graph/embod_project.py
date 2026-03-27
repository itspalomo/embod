import cadquery as cq

from embod import CollisionDef, PrintProfile, Project

project = Project("bad_robot_graph_case")
robot = project.robot("bad_robot_graph_case")

project.part(
    name="body",
    geometry=cq.Workplane().box(60.0, 40.0, 12.0),
    print_profile=PrintProfile(process="fdm", material="PLA"),
    tags=["printable"],
)

robot.link(
    name="base_link",
    parts=["body"],
    collision=CollisionDef.box(60.0, 40.0, 12.0),
)
robot.joint(
    name="broken_joint",
    parent="base_link",
    child="missing_link",
    joint_type="fixed",
)
