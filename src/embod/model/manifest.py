from __future__ import annotations

from dataclasses import dataclass, field

from embod.model.schema import SchemaModel


@dataclass(slots=True, frozen=True)
class EntityBounds(SchemaModel):
    x_mm: float
    y_mm: float
    z_mm: float


@dataclass(slots=True, frozen=True)
class GeometryStats(SchemaModel):
    volume_mm3: float
    is_solid: bool
    solid_count: int


@dataclass(slots=True, frozen=True)
class ExportRecord(SchemaModel):
    format: str
    path: str


@dataclass(slots=True, frozen=True)
class PlacementCandidateManifest(SchemaModel):
    strategy: str
    selector: str
    score: float
    origin_xyz_mm: tuple[float, float, float]
    origin_rpy_deg: tuple[float, float, float]
    score_breakdown: dict[str, float]
    warnings: list[str] = field(default_factory=list)
    interface: str | None = None


@dataclass(slots=True, frozen=True)
class PlacementDecisionManifest(SchemaModel):
    strategy: str
    selector: str
    score: float
    origin_xyz_mm: tuple[float, float, float]
    origin_rpy_deg: tuple[float, float, float]
    interface: str | None = None


@dataclass(slots=True, frozen=True)
class OperationManifest(SchemaModel):
    name: str
    kind: str
    summary: str
    status: str
    warnings: list[str] = field(default_factory=list)
    edit_failures: list[str] = field(default_factory=list)
    selected_placement: PlacementDecisionManifest | None = None
    placement_candidates: list[PlacementCandidateManifest] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class PartManifest(SchemaModel):
    name: str
    tags: list[str]
    interfaces: list[str]
    material: str | None
    notes: str | None
    bounds: EntityBounds
    geometry: GeometryStats
    source_type: str
    resolved_source_kind: str
    mesh_profile: dict[str, float]
    print_profile: (
        dict[str, str | float | bool | tuple[float, float, float] | None] | None
    )
    operations: list[OperationManifest] = field(default_factory=list)
    edit_failures: list[str] = field(default_factory=list)
    exports: list[ExportRecord] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class AssetManifest(SchemaModel):
    name: str
    kind: str
    source_kind: str
    path: str
    tags: list[str]
    printable: bool
    exists: bool
    bounds: EntityBounds | None = None
    mesh_profile: dict[str, float] | None = None
    exports: list[ExportRecord] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class AssemblyComponentManifest(SchemaModel):
    name: str
    ref: str
    translation_mm: tuple[float, float, float]
    rotation_rpy_deg: tuple[float, float, float]
    color: str | None = None


@dataclass(slots=True, frozen=True)
class AssemblyManifest(SchemaModel):
    name: str
    tags: list[str]
    components: list[AssemblyComponentManifest]
    bounds: EntityBounds | None = None
    exports: list[ExportRecord] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class CollisionManifest(SchemaModel):
    kind: str
    origin_xyz_mm: tuple[float, float, float]
    origin_rpy_deg: tuple[float, float, float]
    size_mm: tuple[float, float, float] | None = None
    radius_mm: float | None = None
    length_mm: float | None = None
    axis: str | None = None
    mesh_asset: str | None = None


@dataclass(slots=True, frozen=True)
class LinkManifest(SchemaModel):
    name: str
    parts: list[str]
    assemblies: list[str]
    tags: list[str]
    collision: CollisionManifest | None = None
    inertial_proxy: CollisionManifest | None = None
    mass_kg: float | None = None


@dataclass(slots=True, frozen=True)
class JointManifest(SchemaModel):
    name: str
    parent: str
    child: str
    joint_type: str
    origin_xyz_mm: tuple[float, float, float]
    origin_rpy_deg: tuple[float, float, float]
    axis_xyz: tuple[float, float, float]
    lower_limit_rad: float | None = None
    upper_limit_rad: float | None = None


@dataclass(slots=True, frozen=True)
class FrameManifest(SchemaModel):
    name: str
    parent: str
    origin_xyz_mm: tuple[float, float, float]
    origin_rpy_deg: tuple[float, float, float]


@dataclass(slots=True, frozen=True)
class SensorManifest(SchemaModel):
    name: str
    kind: str
    frame: str
    params: dict[str, str | float | int | bool]


@dataclass(slots=True, frozen=True)
class RobotManifest(SchemaModel):
    name: str
    links: list[LinkManifest]
    joints: list[JointManifest]
    frames: list[FrameManifest]
    sensors: list[SensorManifest]
    exports: list[ExportRecord] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class InterfaceManifest(SchemaModel):
    name: str
    kind: str
    target: str | None
    origin_xyz_mm: tuple[float, float, float]
    origin_rpy_deg: tuple[float, float, float]
    surface_selector: str | None
    allowed_operation_kinds: list[str]
    clearance_mm: float | None
    params: dict[str, str | float | int | bool]


@dataclass(slots=True, frozen=True)
class SnapshotRecord(SchemaModel):
    scene: str
    subject: str
    view: str
    image_path: str
    metadata_path: str


@dataclass(slots=True, frozen=True)
class SnapshotMetadata(SchemaModel):
    scene: str
    subject: str
    view: str
    camera_position: tuple[float, float, float]
    camera_target: tuple[float, float, float]
    image_size: tuple[int, int]


@dataclass(slots=True, frozen=True)
class PrintabilityWarning(SchemaModel):
    code: str
    subject: str
    message: str


@dataclass(slots=True, frozen=True)
class PrintReport(SchemaModel):
    schema_version: str = "embod.print_report.v1"
    warnings: list[PrintabilityWarning] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class BuildMetadata(SchemaModel):
    project_name: str
    units: str
    source_path: str
    build_dir: str
    params: dict[str, str]


@dataclass(slots=True, frozen=True)
class BuildOutputs(SchemaModel):
    manifest_path: str
    exports: list[ExportRecord] = field(default_factory=list)
    snapshots: list[SnapshotRecord] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class BuildManifest(SchemaModel):
    metadata: BuildMetadata
    interfaces: list[InterfaceManifest]
    parts: list[PartManifest]
    assets: list[AssetManifest]
    assemblies: list[AssemblyManifest]
    robots: list[RobotManifest]
    outputs: BuildOutputs
    schema_version: str = "embod.build.v1"


@dataclass(slots=True, frozen=True)
class CapabilitiesReport(SchemaModel):
    commands: list[str]
    export_formats: list[str]
    snapshot_scenes: list[str]
    extras: dict[str, bool]
    schema_version: str = "embod.capabilities.v1"


@dataclass(slots=True, frozen=True)
class FixtureExpectation(SchemaModel):
    scene: str
    subject: str
    view: str


@dataclass(slots=True, frozen=True)
class FixtureAssertionSet(SchemaModel):
    expected_project_name: str
    expected_parts: list[str] = field(default_factory=list)
    expected_assemblies: list[str] = field(default_factory=list)
    expected_robots: list[str] = field(default_factory=list)
    required_diagnostic_codes: list[str] = field(default_factory=list)
    required_export_formats: list[str] = field(default_factory=list)
    snapshots: list[FixtureExpectation] = field(default_factory=list)
