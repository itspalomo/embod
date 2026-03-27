import cadquery as cq

from embod import PrintProfile, Project

project = Project("simple_bracket_case")

project.part(
    name="bracket",
    geometry=(cq.Workplane().box(42.0, 24.0, 4.0).faces(">Z").workplane().hole(4.0)),
    print_profile=PrintProfile(
        process="fdm",
        material="PETG",
        layer_height_mm=0.2,
        nozzle_mm=0.4,
        orientation="flat",
        max_build_volume_mm=(256.0, 256.0, 256.0),
    ),
    tags=["printable"],
)
