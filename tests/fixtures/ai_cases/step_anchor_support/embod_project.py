from embod import FeaturePlacement, GeometrySource, PrintProfile, Project, SupportOp

project = Project("step_anchor_support_case")

project.asset(
    name="camera_block",
    path="fixture_asset.step",
    kind="step",
    tags=["vendor"],
)
project.interface(
    name="mount_anchor",
    kind="mount_face",
    target="camera_block",
    origin_xyz=(0.0, 0.0, 4.0),
    surface_selector=">Z",
    allowed_operation_kinds=["support"],
    clearance_mm=1.5,
)
project.part(
    name="camera_adapter",
    geometry=GeometrySource.imported_step("camera_block"),
    operations=[
        SupportOp(
            name="multiboard_adapter",
            style="multiboard",
            width_mm=14.0,
            height_mm=10.0,
            thickness_mm=4.0,
            hole_diameter_mm=3.0,
            hole_spacing_mm=8.0,
            placement=FeaturePlacement(interface="mount_anchor"),
        )
    ],
    print_profile=PrintProfile(process="fdm", material="PETG", orientation="flat"),
    tags=["printable"],
)
