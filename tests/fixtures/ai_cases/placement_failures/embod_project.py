import cadquery as cq

from embod import FeaturePlacement, PrintProfile, Project, TextOp

project = Project("placement_failures_case")

project.part(
    name="fragile_plate",
    geometry=cq.Workplane("XY").box(24.0, 12.0, 2.0),
    operations=[
        TextOp(
            name="oversized",
            text="TOO BIG",
            font_size_mm=10.0,
            depth_mm=1.2,
            mode="engrave",
            placement=FeaturePlacement(
                surface_selector=">Z",
                min_clearance_mm=3.0,
            ),
        ),
        TextOp(
            name="too_deep",
            text="I",
            font_size_mm=4.0,
            depth_mm=1.6,
            mode="engrave",
            placement=FeaturePlacement(surface_selector=">Z"),
        ),
    ],
    print_profile=PrintProfile(process="fdm", material="PLA", orientation="flat"),
    tags=["printable"],
)
