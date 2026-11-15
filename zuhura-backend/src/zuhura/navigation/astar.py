"""
A* path finding over the MOLA elevation model.

The idea is simple: cut the area around the two points into a grid of cells,
work out how steep and how rough each cell is, forbid cells a wheeled vehicle
could not drive over, and let A* find the cheapest way through the rest.

Steps
  1. Read a block of the MOLA MEGDR DEM (128 px/deg, about 463 m per pixel)
     that covers both points plus a margin, so the path has room to go around
     obstacles.
  2. For every pixel compute
       slope     - from the elevation gradient (degrees)
       roughness - Terrain Ruggedness Index: mean height difference to the
                   8 neighbours (Riley et al., 1999), in metres.
  3. If the block is large, average it down so the grid stays below MAX_GRID
     cells per side (keeps the search fast).
  4. A cell is blocked if its slope or roughness is above the vehicle limit.
  5. Run A* on the 8-connected grid. Moving to a cell costs
         distance * (1 + SLOPE_WEIGHT * (slope / max_slope)^2
                       + ROUGH_WEIGHT * (roughness / max_roughness)^2)
     plus a penalty for climbing. The heuristic is the straight-line distance
     to the goal; every step costs at least its distance, so the heuristic
     never overestimates and A* returns the cheapest path on this grid.
  6. Straighten the zig-zag grid path: skip intermediate cells when the
     straight line between two path points is no more expensive.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

try:
    from osgeo import gdal

    gdal.UseExceptions()
except ImportError:  # GDAL is optional in some test environments
    gdal = None

MARS_RADIUS_M = 3_396_000.0  # sphere radius used by the MOLA MEGDR products
PIXELS_PER_DEGREE = 128
PIXEL_SIZE_M = 463.0576672
DEM_TOP_LAT = 88.0           # the global COG covers 88N to 88S

MAX_GRID = 300               # max cells per side after downsampling
MAX_ROUTE_KM = 600.0
SLOPE_WEIGHT = 4.0
ROUGH_WEIGHT = 2.0
CLIMB_WEIGHT = 3.0           # extra cost per metre climbed, relative to a metre driven

DEFAULT_DEM = (
    Path(__file__).resolve().parents[4]
    / "zuhura-data/data/processed/mola/global_v3/mola_global_meg128_cog.tif"
)

# 8 neighbours: (row step, column step)
NEIGHBOURS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]


class NoPathError(ValueError):
    """Raised when the destination cannot be reached under the vehicle limits."""


@dataclass
class Vehicle:
    name: str
    max_slope_deg: float      # steepest slope it may drive on
    max_roughness_m: float    # roughest ground (TRI on 463 m pixels) it may drive on


VEHICLES = {
    "car": Vehicle("Car-like vehicle", max_slope_deg=10.0, max_roughness_m=60.0),
    "rover": Vehicle("Rover (Perseverance class)", max_slope_deg=20.0, max_roughness_m=120.0),
}


@dataclass
class Grid:
    elevation: np.ndarray     # metres, rows go north to south
    slope: np.ndarray         # degrees
    roughness: np.ndarray     # metres (TRI)
    lat0: float               # latitude of the centre of row 0
    lon0: float               # longitude of the centre of column 0 (may be < 0 or > 360)
    step_deg: float           # cell size in degrees
    cell_m: float             # cell size in metres north-south

    def latlon(self, r: int, c: int) -> Tuple[float, float]:
        return self.lat0 - r * self.step_deg, self.lon0 + c * self.step_deg

    def cell(self, lat: float, lon: float) -> Tuple[int, int]:
        r = int(round((self.lat0 - lat) / self.step_deg))
        c = int(round((lon - self.lon0) / self.step_deg))
        rows, cols = self.elevation.shape
        return min(max(r, 0), rows - 1), min(max(c, 0), cols - 1)

    def dx_m(self, r: int) -> float:
        """East-west cell size shrinks with cos(latitude)."""
        lat = self.lat0 - r * self.step_deg
        return self.cell_m * max(math.cos(math.radians(lat)), 0.05)


# ----------------------------------------------------------------------------
# DEM reading
# ----------------------------------------------------------------------------

def read_dem_block(row0: int, col0: int, rows: int, cols: int, dem_path: Path = DEFAULT_DEM) -> np.ndarray:
    """Read a block of the global DEM. Columns wrap around at 0/360 E."""
    if gdal is None or not dem_path.exists():
        raise RuntimeError("The MOLA elevation model is not available on the server.")

    ds = gdal.Open(str(dem_path))
    band = ds.GetRasterBand(1)
    width, height = ds.RasterXSize, ds.RasterYSize

    row0 = max(0, row0)
    rows = min(rows, height - row0)

    pieces = []
    c, remaining = col0 % width, cols
    while remaining > 0:
        n = min(remaining, width - c)
        pieces.append(band.ReadAsArray(c, row0, n, rows))
        remaining -= n
        c = 0
    return np.hstack(pieces).astype(np.float64)


def block_mean(a: np.ndarray, f: int) -> np.ndarray:
    """Average f x f blocks (downsampling)."""
    if f == 1:
        return a
    rows, cols = (a.shape[0] // f) * f, (a.shape[1] // f) * f
    return a[:rows, :cols].reshape(rows // f, f, cols // f, f).mean(axis=(1, 3))


def build_grid(start: Tuple[float, float], goal: Tuple[float, float], dem_path: Path = DEFAULT_DEM) -> Grid:
    (lat1, lon1), (lat2, lon2) = start, goal

    span = max(abs(lat2 - lat1), abs(lon2 - lon1))
    margin = max(0.15, 0.4 * span)  # room to drive around obstacles
    north = min(max(lat1, lat2) + margin, DEM_TOP_LAT)
    south = max(min(lat1, lat2) - margin, -DEM_TOP_LAT)
    west = min(lon1, lon2) - margin
    east = max(lon1, lon2) + margin

    row0 = int(math.floor((DEM_TOP_LAT - north) * PIXELS_PER_DEGREE))
    col0 = int(math.floor(west * PIXELS_PER_DEGREE))
    rows = int(math.ceil((north - south) * PIXELS_PER_DEGREE)) + 1
    cols = int(math.ceil((east - west) * PIXELS_PER_DEGREE)) + 1

    elevation = read_dem_block(row0, col0, rows, cols, dem_path)

    # Slope and roughness are measured on the full-resolution DEM, so the vehicle
    # limits mean the same thing however large the search area is.
    lats = DEM_TOP_LAT - (row0 + 0.5 + np.arange(elevation.shape[0])) / PIXELS_PER_DEGREE
    dx = PIXEL_SIZE_M * np.maximum(np.cos(np.radians(lats)), 0.05)
    slope = slope_degrees(elevation, dx, PIXEL_SIZE_M)
    roughness = terrain_ruggedness(elevation)

    # Long routes: average f x f pixel blocks so the grid stays below MAX_GRID per side.
    f = max(1, math.ceil(max(elevation.shape) / MAX_GRID))
    elevation, slope, roughness = (block_mean(a, f) for a in (elevation, slope, roughness))

    step_deg = f / PIXELS_PER_DEGREE
    # Centre of the first (possibly averaged) cell.
    lat0 = DEM_TOP_LAT - (row0 + f / 2) / PIXELS_PER_DEGREE
    lon0 = (col0 + f / 2) / PIXELS_PER_DEGREE
    cell_m = PIXEL_SIZE_M * f
    return Grid(elevation, slope, roughness, lat0, lon0, step_deg, cell_m)


# ----------------------------------------------------------------------------
# Terrain measures
# ----------------------------------------------------------------------------

def slope_degrees(z: np.ndarray, dx_per_row: np.ndarray, dy: float) -> np.ndarray:
    """Slope from central differences; dx varies by row because of latitude."""
    dz_dy, dz_dx = np.gradient(z)
    dz_dx = dz_dx / dx_per_row[:, None]
    dz_dy = dz_dy / dy
    return np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))


def terrain_ruggedness(z: np.ndarray) -> np.ndarray:
    """Terrain Ruggedness Index: mean absolute height difference to the 8 neighbours."""
    p = np.pad(z, 1, mode="edge")
    rows, cols = z.shape
    total = np.zeros_like(z)
    for dr, dc in NEIGHBOURS:
        total += np.abs(p[1 + dr:1 + dr + rows, 1 + dc:1 + dc + cols] - z)
    return total / 8.0


# ----------------------------------------------------------------------------
# A*
# ----------------------------------------------------------------------------

def blocked_mask(grid: Grid, vehicle: Vehicle) -> np.ndarray:
    return (grid.slope > vehicle.max_slope_deg) | (grid.roughness > vehicle.max_roughness_m)


def terrain_factor(grid: Grid, vehicle: Vehicle) -> np.ndarray:
    """Per-cell multiplier >= 1 applied to the distance driven through the cell."""
    s = grid.slope / vehicle.max_slope_deg
    r = grid.roughness / vehicle.max_roughness_m
    return 1.0 + SLOPE_WEIGHT * s ** 2 + ROUGH_WEIGHT * r ** 2


def step_length_m(grid: Grid, r: int, dr: int, dc: int) -> float:
    return math.hypot(dr * grid.cell_m, dc * grid.dx_m(r))


def astar(grid: Grid, start: Tuple[int, int], goal: Tuple[int, int], vehicle: Vehicle) -> Tuple[List[Tuple[int, int]], int]:
    """Returns (path as list of cells, number of cells expanded)."""
    rows, cols = grid.elevation.shape
    blocked = blocked_mask(grid, vehicle)
    blocked[start] = False  # always allow leaving the start and entering the goal
    blocked[goal] = False
    factor = terrain_factor(grid, vehicle)
    z = grid.elevation
    max_grade = math.tan(math.radians(vehicle.max_slope_deg))

    # Heuristic: straight-line distance using the smallest east-west cell size in the grid
    # (the row nearest the pole). That makes it a lower bound on any real path, so A* is optimal.
    dx_min = min(grid.dx_m(0), grid.dx_m(rows - 1))

    def h(cell: Tuple[int, int]) -> float:
        return math.hypot((cell[0] - goal[0]) * grid.cell_m, (cell[1] - goal[1]) * dx_min)

    g = {start: 0.0}
    came_from = {}
    open_heap = [(h(start), 0.0, start)]
    closed = set()

    while open_heap:
        _, g_cur, cur = heapq.heappop(open_heap)
        if cur in closed:
            continue
        if cur == goal:
            path = [cur]
            while cur in came_from:
                cur = came_from[cur]
                path.append(cur)
            return path[::-1], len(closed)
        closed.add(cur)

        r, c = cur
        for dr, dc in NEIGHBOURS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < rows and 0 <= nc < cols) or blocked[nr, nc] or (nr, nc) in closed:
                continue
            dist = step_length_m(grid, r, dr, dc)
            climb = z[nr, nc] - z[r, c]
            if abs(climb) / dist > max_grade:
                continue  # this particular step is too steep
            cost = dist * factor[nr, nc] + CLIMB_WEIGHT * max(climb, 0.0)
            new_g = g_cur + cost
            if new_g < g.get((nr, nc), math.inf):
                g[(nr, nc)] = new_g
                came_from[(nr, nc)] = cur
                heapq.heappush(open_heap, (new_g + h((nr, nc)), new_g, (nr, nc)))

    raise NoPathError(
        "No drivable path was found. The terrain between the two points is too steep or rough "
        "for this vehicle; try the rover setting or points closer together."
    )


# ----------------------------------------------------------------------------
# Path straightening
# ----------------------------------------------------------------------------

def line_cells(a: Tuple[int, int], b: Tuple[int, int]) -> List[Tuple[int, int]]:
    """Cells on the straight line from a to b (inclusive)."""
    n = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
    if n == 0:
        return [a]
    return [
        (round(a[0] + (b[0] - a[0]) * i / n), round(a[1] + (b[1] - a[1]) * i / n))
        for i in range(n + 1)
    ]


def walk_cost(grid: Grid, cells: List[Tuple[int, int]], vehicle: Vehicle, blocked: np.ndarray, factor: np.ndarray) -> float:
    max_grade = math.tan(math.radians(vehicle.max_slope_deg))
    total = 0.0
    for (r, c), (nr, nc) in zip(cells, cells[1:]):
        if blocked[nr, nc]:
            return math.inf
        dist = step_length_m(grid, r, nr - r, nc - c)
        climb = grid.elevation[nr, nc] - grid.elevation[r, c]
        if dist > 0 and abs(climb) / dist > max_grade:
            return math.inf
        total += dist * factor[nr, nc] + CLIMB_WEIGHT * max(climb, 0.0)
    return total


def straighten(grid: Grid, path: List[Tuple[int, int]], vehicle: Vehicle, look_ahead: int = 40) -> List[Tuple[int, int]]:
    """Replace zig-zags with straight runs when the straight run costs no more."""
    blocked = blocked_mask(grid, vehicle)
    blocked[path[0]] = blocked[path[-1]] = False
    factor = terrain_factor(grid, vehicle)

    out = [path[0]]
    i = 0
    while i < len(path) - 1:
        best = i + 1
        for j in range(min(len(path) - 1, i + look_ahead), i + 1, -1):
            straight = line_cells(path[i], path[j])
            if walk_cost(grid, straight, vehicle, blocked, factor) <= walk_cost(grid, path[i:j + 1], vehicle, blocked, factor):
                best = j
                break
        out.extend(line_cells(path[i], path[best])[1:])
        i = best
    return out


# ----------------------------------------------------------------------------
# Public entry point
# ----------------------------------------------------------------------------

def surface_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * MARS_RADIUS_M * math.asin(math.sqrt(a)) / 1000.0


def plan_path(
    start_lat: float,
    start_lon: float,
    goal_lat: float,
    goal_lon: float,
    vehicle_key: str = "car",
    dem_path: Path = DEFAULT_DEM,
) -> dict:
    vehicle = VEHICLES.get(vehicle_key, VEHICLES["car"])

    for lat in (start_lat, goal_lat):
        if abs(lat) > 85.0:
            raise ValueError("Points must lie between 85° S and 85° N.")

    start_lon %= 360.0
    goal_lon %= 360.0
    # Take the short way round if the points straddle 0/360 E.
    if goal_lon - start_lon > 180.0:
        goal_lon -= 360.0
    elif start_lon - goal_lon > 180.0:
        goal_lon += 360.0

    direct_km = surface_distance_km(start_lat, start_lon, goal_lat, goal_lon)
    if direct_km > MAX_ROUTE_KM:
        raise ValueError(f"Points are {direct_km:.0f} km apart. Pick points less than {MAX_ROUTE_KM:.0f} km apart.")
    if direct_km < 0.5:
        raise ValueError("The two points are too close together.")

    grid = build_grid((start_lat, start_lon), (goal_lat, goal_lon), dem_path)
    start_cell = grid.cell(start_lat, start_lon)
    goal_cell = grid.cell(goal_lat, goal_lon)

    raw_path, expanded = astar(grid, start_cell, goal_cell, vehicle)
    path = straighten(grid, raw_path, vehicle)

    waypoints = []
    total_m = gain = loss = 0.0
    prev = None
    for r, c in path:
        lat, lon = grid.latlon(r, c)
        elev = float(grid.elevation[r, c])
        if prev is not None:
            total_m += surface_distance_km(prev[0], prev[1], lat, lon) * 1000.0
            dz = elev - prev[2]
            gain += max(dz, 0.0)
            loss += max(-dz, 0.0)
        waypoints.append({
            "latitude": round(lat, 5),
            "longitude": round(lon % 360.0, 5),
            "elevation_m": round(elev, 1),
            "distance_km": round(total_m / 1000.0, 3),
            "slope_degrees": round(float(grid.slope[r, c]), 2),
            "roughness_tri": round(float(grid.roughness[r, c]), 1),
        })
        prev = (lat, lon, elev)

    slopes = [w["slope_degrees"] for w in waypoints]
    blocked = blocked_mask(grid, vehicle)
    return {
        "route_id": f"astar_{vehicle_key}",
        "name": "A* path",
        "description": f"Cheapest path for a {vehicle.name.lower()} avoiding slopes over "
                       f"{vehicle.max_slope_deg:.0f}° and rough ground.",
        "vehicle": vehicle_key,
        "max_slope_limit_deg": vehicle.max_slope_deg,
        "max_roughness_limit_m": vehicle.max_roughness_m,
        "total_distance_km": round(total_m / 1000.0, 2),
        "direct_distance_km": round(direct_km, 2),
        "detour_factor": round(total_m / 1000.0 / direct_km, 2),
        "elevation_gain_m": round(gain),
        "elevation_loss_m": round(loss),
        "max_slope_degrees": round(max(slopes), 1),
        "mean_slope_degrees": round(sum(slopes) / len(slopes), 1),
        "waypoints": waypoints,
        "grid": {
            "rows": int(grid.elevation.shape[0]),
            "cols": int(grid.elevation.shape[1]),
            "cell_size_m": round(grid.cell_m),
            "blocked_percent": round(100.0 * float(blocked.mean()), 1),
            "cells_expanded": expanded,
        },
        "dataset": "MGS MOLA MEGDR 128 px/deg (463 m/px)",
    }
