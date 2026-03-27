from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import cadquery as cq

from embod.exporters.cadquery_export import export_part
from embod.model.core import MeshProfile, Part


def test_export_part_passes_mesh_profile_to_stl_export(tmp_path: Path) -> None:
    part = Part(
        name="disk",
        geometry=cq.Workplane().circle(12.0).extrude(4.0),
        mesh_profile=MeshProfile(tolerance_mm=0.02, angular_tolerance_rad=0.01),
    )
    export_calls: list[tuple[str, dict[str, float]]] = []
    original_export = cq.Workplane.export

    def recording_export(
        self: cq.Workplane,
        path: str,
        *args: object,
        **kwargs: object,
    ) -> None:
        assert not args
        tolerance = kwargs.get("tolerance", 0.1)
        angular_tolerance = kwargs.get("angularTolerance", 0.1)
        opt = kwargs.get("opt")
        assert isinstance(tolerance, float)
        assert isinstance(angular_tolerance, float)
        assert opt is None or isinstance(opt, dict)
        export_calls.append(
            (
                Path(path).suffix,
                {
                    "tolerance": tolerance,
                    "angularTolerance": angular_tolerance,
                },
            )
        )
        original_export(
            self,
            path,
            tolerance=tolerance,
            angularTolerance=angular_tolerance,
            opt=opt,
        )

    with patch.object(cq.Workplane, "export", new=recording_export):
        manifest = export_part(part, build_dir=tmp_path)

    assert manifest.mesh_profile == {
        "tolerance_mm": 0.02,
        "angular_tolerance_rad": 0.01,
    }
    assert export_calls == [
        (".step", {"tolerance": 0.1, "angularTolerance": 0.1}),
        (".stl", {"tolerance": 0.02, "angularTolerance": 0.01}),
    ]
