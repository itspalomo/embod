import cadquery as cq

from embod import PrintProfile, Project

project = Project("simple_bracket")

bracket = cq.Workplane().box(48.0, 28.0, 4.0).faces(">Z").workplane().hole(4.2)

project.part(
    name="bracket",
    geometry=bracket,
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
