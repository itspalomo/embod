import cadquery as cq

from embod import FeaturePlacement, PrintProfile, Project, TextOp

project = Project("signage_panel_case")

project.part(
    name="sign_panel",
    geometry=cq.Workplane("XY").box(90.0, 50.0, 4.0),
    operations=[
        TextOp(
            name="title",
            text="embod",
            font_size_mm=16.0,
            depth_mm=1.2,
            mode="emboss",
            placement=FeaturePlacement(
                surface_selector=">Z",
                offset_mm=(0.0, 8.0, 0.0),
            ),
        ),
        TextOp(
            name="detail",
            text="cad",
            font_size_mm=8.0,
            depth_mm=0.8,
            mode="engrave",
            placement=FeaturePlacement(
                surface_selector=">Z",
                offset_mm=(0.0, -10.0, 0.0),
            ),
        ),
        TextOp(
            name="cut",
            text="AI",
            font_size_mm=9.0,
            depth_mm=1.0,
            mode="cutout",
            placement=FeaturePlacement(
                surface_selector=">Z",
                offset_mm=(26.0, 0.0, 0.0),
            ),
        ),
    ],
    print_profile=PrintProfile(
        process="fdm",
        material="PETG",
        orientation="flat",
        support_strategy="avoid",
    ),
    tags=["printable"],
)
