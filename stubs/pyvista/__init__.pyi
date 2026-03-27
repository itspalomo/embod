class PolyData:
    bounds: tuple[float, float, float, float, float, float]
    volume: float
    is_manifold: bool
    n_cells: int
    def copy(self, deep: bool = ...) -> PolyData: ...
    def translate(
        self,
        xyz: tuple[float, float, float],
        transform_all_input_vectors: bool = ...,
        inplace: bool = ...,
    ) -> PolyData: ...
    def rotate_x(
        self,
        angle: float,
        point: tuple[float, float, float] | None = ...,
        transform_all_input_vectors: bool = ...,
        inplace: bool = ...,
    ) -> PolyData: ...
    def rotate_y(
        self,
        angle: float,
        point: tuple[float, float, float] | None = ...,
        transform_all_input_vectors: bool = ...,
        inplace: bool = ...,
    ) -> PolyData: ...
    def rotate_z(
        self,
        angle: float,
        point: tuple[float, float, float] | None = ...,
        transform_all_input_vectors: bool = ...,
        inplace: bool = ...,
    ) -> PolyData: ...
    def scale(
        self,
        xyz: float | tuple[float, float, float],
        transform_all_input_vectors: bool = ...,
        inplace: bool = ...,
        point: tuple[float, float, float] | None = ...,
    ) -> PolyData: ...
    def triangulate(self, inplace: bool = ...) -> PolyData: ...
    def boolean_union(
        self, other_mesh: PolyData, tolerance: float = ..., progress_bar: bool = ...
    ) -> PolyData: ...
    def boolean_difference(
        self, other_mesh: PolyData, tolerance: float = ..., progress_bar: bool = ...
    ) -> PolyData: ...
    def save(self, filename: str) -> None: ...

class Plotter:
    camera_position: object
    def __init__(
        self, off_screen: bool = ..., window_size: tuple[int, int] | None = ...
    ) -> None: ...
    def set_background(self, color: str) -> None: ...
    def add_mesh(
        self,
        mesh: object,
        color: str = ...,
        show_edges: bool = ...,
        opacity: float = ...,
    ) -> None: ...
    def show(self, screenshot: str | None = ..., auto_close: bool = ...) -> None: ...
    def screenshot(
        self, filename: str | None = ..., return_img: bool = ...
    ) -> object: ...
    def close(self) -> None: ...

def read(path: str) -> PolyData: ...
def Box(
    bounds: tuple[float, float, float, float, float, float] = ...,
    level: int | tuple[int, int, int] = ...,
    quads: bool = ...,
) -> PolyData: ...
def Cylinder(
    center: tuple[float, float, float] = ...,
    direction: tuple[float, float, float] = ...,
    radius: float = ...,
    height: float = ...,
    resolution: int = ...,
    capping: bool = ...,
) -> PolyData: ...
def Sphere(
    radius: float = ...,
    center: tuple[float, float, float] = ...,
    direction: tuple[float, float, float] = ...,
    theta_resolution: int = ...,
    phi_resolution: int = ...,
    start_theta: float = ...,
    end_theta: float = ...,
    start_phi: float = ...,
    end_phi: float = ...,
) -> PolyData: ...
def Text3D(
    string: str,
    depth: float | None = ...,
    width: float | None = ...,
    height: float | None = ...,
    center: tuple[float, float, float] = ...,
    normal: tuple[float, float, float] = ...,
) -> PolyData: ...
