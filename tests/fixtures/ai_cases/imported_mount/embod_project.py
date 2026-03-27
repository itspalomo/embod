import cadquery as cq

from embod import PrintProfile, Project

project = Project("imported_mount_case")

project.asset(
    name="camera_block",
    path="fixture_asset.step",
    kind="step",
    tags=["vendor"],
)

project.part(
    name="mount_shell",
    geometry=(cq.Workplane().box(34.0, 34.0, 10.0).faces(">Z").workplane().hole(6.0)),
    print_profile=PrintProfile(process="fdm", material="PLA"),
    tags=["printable"],
)
