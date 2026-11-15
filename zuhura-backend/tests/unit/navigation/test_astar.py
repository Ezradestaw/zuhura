import numpy as np
import pytest

from zuhura.navigation.astar import (
    PIXEL_SIZE_M,
    VEHICLES,
    Grid,
    NoPathError,
    astar,
    slope_degrees,
    straighten,
    terrain_ruggedness,
)


def make_grid(z: np.ndarray) -> Grid:
    dx = np.full(z.shape[0], PIXEL_SIZE_M)
    return Grid(
        elevation=z,
        slope=slope_degrees(z, dx, PIXEL_SIZE_M),
        roughness=terrain_ruggedness(z),
        lat0=0.5,
        lon0=10.0,
        step_deg=1 / 128,
        cell_m=PIXEL_SIZE_M,
    )


def test_flat_ground_gives_straight_line():
    grid = make_grid(np.zeros((20, 20)))
    path, _ = astar(grid, (10, 0), (10, 19), VEHICLES["car"])
    assert all(r == 10 for r, _ in path)
    assert len(path) == 20


def test_path_goes_around_a_ridge():
    z = np.zeros((30, 30))
    z[0:25, 14:16] = 2000.0  # steep wall with a gap at the bottom
    grid = make_grid(z)
    path, _ = astar(grid, (5, 2), (5, 27), VEHICLES["car"])
    assert max(r for r, _ in path) >= 25  # had to go through the gap
    assert all(z[cell] == 0.0 for cell in path)


def test_no_path_when_fully_blocked():
    z = np.zeros((20, 20))
    z[:, 9:11] = 3000.0
    with pytest.raises(NoPathError):
        astar(make_grid(z), (10, 2), (10, 17), VEHICLES["car"])


def test_straighten_keeps_endpoints_and_removes_zigzag():
    grid = make_grid(np.zeros((20, 20)))
    zigzag = [(0, 0), (1, 1), (1, 2), (2, 3), (2, 4), (3, 5)]
    out = straighten(grid, zigzag, VEHICLES["car"])
    assert out[0] == zigzag[0] and out[-1] == zigzag[-1]
    assert len(out) <= len(zigzag)


def test_slope_of_known_ramp():
    z = np.tile(np.arange(10) * PIXEL_SIZE_M * np.tan(np.radians(10)), (10, 1))
    s = slope_degrees(z, np.full(10, PIXEL_SIZE_M), PIXEL_SIZE_M)
    assert np.allclose(s[:, 1:-1], 10.0, atol=0.01)
