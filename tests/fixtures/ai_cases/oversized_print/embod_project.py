import cadquery as cq

from embod import PrintProfile, Project

project = Project("oversized_print_case")

project.part(
    name="giant_plate",
    geometry=cq.Workplane().box(320.0, 120.0, 4.0),
    print_profile=PrintProfile(
        process="fdm",
        material="PLA",
        max_build_volume_mm=(256.0, 256.0, 256.0),
    ),
    tags=["printable"],
)
