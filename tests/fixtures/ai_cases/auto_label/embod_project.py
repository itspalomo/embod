import cadquery as cq

from embod import PrintProfile, Project, TextOp

project = Project("auto_label_case")

project.part(
    name="label_plate",
    geometry=cq.Workplane("XY").box(90.0, 40.0, 6.0),
    operations=[
        TextOp(
            name="auto_label",
            text="AUTO",
            font_size_mm=14.0,
            depth_mm=1.2,
        )
    ],
    print_profile=PrintProfile(
        process="fdm",
        material="PETG",
        orientation="flat",
        support_strategy="avoid",
    ),
    tags=["printable"],
)
