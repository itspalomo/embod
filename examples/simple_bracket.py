import cadquery as cq

from embod import MeshProfile, PrintProfile, Project

project = Project("simple_bracket")

base = cq.Workplane("XY").box(68.0, 34.0, 6.0).edges("|Z").fillet(3.0)
upright = (
    cq.Workplane("XY")
    .box(68.0, 6.0, 42.0)
    .translate((0.0, 14.0, 18.0))
    .edges("|Z")
    .fillet(2.0)
)
left_gusset = (
    cq.Workplane("XZ")
    .polyline([(-22.0, 0.0), (-22.0, 24.0), (0.0, 0.0)])
    .close()
    .extrude(6.0)
    .translate((0.0, 7.0, 0.0))
)
right_gusset = (
    cq.Workplane("XZ")
    .polyline([(22.0, 0.0), (22.0, 24.0), (0.0, 0.0)])
    .close()
    .extrude(6.0)
    .translate((0.0, 7.0, 0.0))
)

bracket = base.union(upright).union(left_gusset).union(right_gusset)
bracket = (
    bracket.faces(">Z")
    .workplane()
    .pushPoints([(-20.0, 0.0), (20.0, 0.0)])
    .cboreHole(5.2, 10.0, 3.0)
)
bracket = (
    bracket.faces(">Y")
    .workplane()
    .pushPoints([(-18.0, 10.0), (18.0, 10.0)])
    .hole(4.3)
)

project.part(
    name="bracket",
    geometry=bracket,
    mesh_profile=MeshProfile(tolerance_mm=0.03, angular_tolerance_rad=0.025),
    print_profile=PrintProfile(
        process="fdm",
        material="PETG",
        layer_height_mm=0.2,
        nozzle_mm=0.4,
        orientation="flat",
        max_build_volume_mm=(256.0, 256.0, 256.0),
    ),
    tags=["printable", "structural"],
)
