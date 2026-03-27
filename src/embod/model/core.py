from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

Vector3 = tuple[float, float, float]


@dataclass(slots=True, frozen=True)
class PrintProfile:
    process: str
    material: str
    layer_height_mm: float | None = None
    nozzle_mm: float | None = None
    orientation: str | None = None
    support_strategy: str | None = None
    max_build_volume_mm: Vector3 | None = None
    split_if_needed: bool = False


@dataclass(slots=True, frozen=True)
class InterfaceDef:
    name: str
    kind: str
    params: dict[str, str | float | int | bool] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class CollisionDef:
    kind: str
    size_mm: Vector3 | None = None
    radius_mm: float | None = None
    length_mm: float | None = None
    axis: str | None = None
    mesh_asset: str | None = None
    origin_xyz_mm: Vector3 = (0.0, 0.0, 0.0)
    origin_rpy_deg: Vector3 = (0.0, 0.0, 0.0)

    @classmethod
    def box(cls, x_mm: float, y_mm: float, z_mm: float) -> CollisionDef:
        return cls(kind="box", size_mm=(x_mm, y_mm, z_mm))

    @classmethod
    def cylinder(
        cls,
        radius_mm: float,
        length_mm: float,
        axis: str = "z",
    ) -> CollisionDef:
        return cls(
            kind="cylinder",
            radius_mm=radius_mm,
            length_mm=length_mm,
            axis=axis,
        )

    @classmethod
    def sphere(cls, radius_mm: float) -> CollisionDef:
        return cls(kind="sphere", radius_mm=radius_mm)

    @classmethod
    def mesh(cls, mesh_asset: str) -> CollisionDef:
        return cls(kind="mesh", mesh_asset=mesh_asset)


@dataclass(slots=True)
class Part:
    name: str
    geometry: object
    print_profile: PrintProfile | None = None
    tags: list[str] = field(default_factory=list)
    interfaces: list[str] = field(default_factory=list)
    material: str | None = None
    notes: str | None = None


@dataclass(slots=True)
class ImportedAsset:
    name: str
    path: Path
    kind: str
    tags: list[str] = field(default_factory=list)
    printable: bool = False


@dataclass(slots=True, frozen=True)
class AssemblyComponent:
    name: str
    ref: str
    translation_mm: Vector3 = (0.0, 0.0, 0.0)
    rotation_rpy_deg: Vector3 = (0.0, 0.0, 0.0)
    color: str | None = None


@dataclass(slots=True)
class Assembly:
    name: str
    components: list[AssemblyComponent] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class Link:
    name: str
    parts: list[str] = field(default_factory=list)
    assemblies: list[str] = field(default_factory=list)
    collision: CollisionDef | None = None
    inertial_proxy: CollisionDef | None = None
    mass_kg: float | None = None
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class Joint:
    name: str
    parent: str
    child: str
    joint_type: str
    origin_xyz_mm: Vector3 = (0.0, 0.0, 0.0)
    origin_rpy_deg: Vector3 = (0.0, 0.0, 0.0)
    axis_xyz: Vector3 = (0.0, 0.0, 1.0)
    lower_limit_rad: float | None = None
    upper_limit_rad: float | None = None


@dataclass(slots=True, frozen=True)
class Frame:
    name: str
    parent: str
    origin_xyz_mm: Vector3 = (0.0, 0.0, 0.0)
    origin_rpy_deg: Vector3 = (0.0, 0.0, 0.0)


@dataclass(slots=True, frozen=True)
class Sensor:
    name: str
    kind: str
    frame: str
    params: dict[str, str | float | int | bool] = field(default_factory=dict)


@dataclass(slots=True)
class Robot:
    name: str
    links: dict[str, Link] = field(default_factory=dict)
    joints: dict[str, Joint] = field(default_factory=dict)
    frames: dict[str, Frame] = field(default_factory=dict)
    sensors: dict[str, Sensor] = field(default_factory=dict)

    def link(
        self,
        name: str,
        *,
        parts: list[str] | None = None,
        assemblies: list[str] | None = None,
        collision: CollisionDef | None = None,
        inertial_proxy: CollisionDef | None = None,
        mass_kg: float | None = None,
        tags: list[str] | None = None,
    ) -> Link:
        entity = Link(
            name=name,
            parts=parts or [],
            assemblies=assemblies or [],
            collision=collision,
            inertial_proxy=inertial_proxy,
            mass_kg=mass_kg,
            tags=tags or [],
        )
        self.links[name] = entity
        return entity

    def joint(
        self,
        name: str,
        *,
        parent: str,
        child: str,
        joint_type: str,
        origin_xyz: Vector3 = (0.0, 0.0, 0.0),
        origin_rpy_deg: Vector3 = (0.0, 0.0, 0.0),
        axis_xyz: Vector3 = (0.0, 0.0, 1.0),
        lower_limit_rad: float | None = None,
        upper_limit_rad: float | None = None,
    ) -> Joint:
        entity = Joint(
            name=name,
            parent=parent,
            child=child,
            joint_type=joint_type,
            origin_xyz_mm=origin_xyz,
            origin_rpy_deg=origin_rpy_deg,
            axis_xyz=axis_xyz,
            lower_limit_rad=lower_limit_rad,
            upper_limit_rad=upper_limit_rad,
        )
        self.joints[name] = entity
        return entity

    def frame(
        self,
        name: str,
        *,
        parent: str,
        origin_xyz: Vector3 = (0.0, 0.0, 0.0),
        origin_rpy_deg: Vector3 = (0.0, 0.0, 0.0),
    ) -> Frame:
        entity = Frame(
            name=name,
            parent=parent,
            origin_xyz_mm=origin_xyz,
            origin_rpy_deg=origin_rpy_deg,
        )
        self.frames[name] = entity
        return entity

    def sensor(
        self,
        name: str,
        *,
        kind: str,
        frame: str,
        params: dict[str, str | float | int | bool] | None = None,
    ) -> Sensor:
        entity = Sensor(name=name, kind=kind, frame=frame, params=params or {})
        self.sensors[name] = entity
        return entity


@dataclass(slots=True)
class Project:
    name: str
    units: str = "mm"
    parts: dict[str, Part] = field(default_factory=dict)
    imported_assets: dict[str, ImportedAsset] = field(default_factory=dict)
    assemblies: dict[str, Assembly] = field(default_factory=dict)
    interfaces: dict[str, InterfaceDef] = field(default_factory=dict)
    robots: dict[str, Robot] = field(default_factory=dict)
    parameters: dict[str, str | float | int | bool] = field(default_factory=dict)

    def param(
        self,
        name: str,
        default: str | float | int | bool,
    ) -> str | float | int | bool:
        self.parameters[name] = default
        return default

    def part(
        self,
        *,
        name: str,
        geometry: object,
        print_profile: PrintProfile | None = None,
        tags: list[str] | None = None,
        interfaces: list[str] | None = None,
        material: str | None = None,
        notes: str | None = None,
    ) -> Part:
        entity = Part(
            name=name,
            geometry=geometry,
            print_profile=print_profile,
            tags=tags or [],
            interfaces=interfaces or [],
            material=material,
            notes=notes,
        )
        self.parts[name] = entity
        return entity

    def asset(
        self,
        *,
        name: str,
        path: str | Path,
        kind: str,
        tags: list[str] | None = None,
        printable: bool = False,
    ) -> ImportedAsset:
        entity = ImportedAsset(
            name=name,
            path=Path(path),
            kind=kind,
            tags=tags or [],
            printable=printable,
        )
        self.imported_assets[name] = entity
        return entity

    def assembly(
        self,
        *,
        name: str,
        components: list[AssemblyComponent] | None = None,
        tags: list[str] | None = None,
    ) -> Assembly:
        entity = Assembly(name=name, components=components or [], tags=tags or [])
        self.assemblies[name] = entity
        return entity

    def interface(
        self,
        *,
        name: str,
        kind: str,
        params: dict[str, str | float | int | bool] | None = None,
    ) -> InterfaceDef:
        entity = InterfaceDef(name=name, kind=kind, params=params or {})
        self.interfaces[name] = entity
        return entity

    def robot(self, name: str) -> Robot:
        entity = Robot(name=name)
        self.robots[name] = entity
        return entity
