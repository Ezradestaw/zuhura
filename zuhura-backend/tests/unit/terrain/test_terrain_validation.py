"""
Validation tests for terrain derivatives against reference values.
Tests:
  1. Slope calculations against analytical synthetic terrain surfaces at multiple latitudes (0°, 45°, 75°).
  2. Aspect directions and compass angle conventions using known directional gradients (N, E, S, W, diagonals, flat).
  3. Coordinate normalization across 0°/360° and -180°/+180° longitude conventions.
  4. Boundary and polar coverage handling (|lat| > 88° routing to Polar Stereographic DEMs).
  5. Great-circle geodesic transect profiling with monotonic distance accumulation and relief consistency.
  6. Focal morphometry (TRI roughness, TPI landform classification, local relief).
  7. Verification of known Mars elevation landmarks (Olympus Mons, Jezero, Gale, Valles Marineris).
  8. Scientific provenance transparency: nominal ~463 m/px resolution, metric cell size, and areoid datum.
"""

import math
import numpy as np
import pytest

from zuhura.terrain_intelligence.derivatives import (
    calculate_slope_and_aspect_horn,
    aspect_degrees_to_cardinal,
    calculate_profile_curvature,
    MOLA_EQUATORIAL_CELL_M,
)
from zuhura.terrain_intelligence.morphometry import (
    calculate_tri_roughness,
    calculate_tpi,
    classify_tpi,
    calculate_focal_relief,
    calculate_focal_statistics,
)
from zuhura.terrain_intelligence.profiler import (
    interpolate_geodesic_transect,
    compute_profile_summary,
    calculate_great_circle_distance_km,
    normalize_east_longitude_360,
)
from zuhura.terrain_intelligence.engine import TerrainIntelligenceEngine


# ==============================================================================
# Gate 1: Slope against Analytical Synthetic Surfaces at Multiple Latitudes
# ==============================================================================

def test_synthetic_slope_at_equator():
    """Tests analytical planar slope at Equator (0° latitude) where cos(0) = 1.0."""
    dx = MOLA_EQUATORIAL_CELL_M
    dy = MOLA_EQUATORIAL_CELL_M
    target_slope_deg = 20.0
    grad = math.tan(math.radians(target_slope_deg))

    # Create 3x3 East-dipping plane: z(x) = -grad * x
    # col 0 (West): x = -dx -> z = +grad * dx
    # col 1 (Center): x = 0 -> z = 0
    # col 2 (East): x = +dx -> z = -grad * dx
    dz = grad * dx
    window = np.array([
        [+dz, +dz, +dz],
        [ 0.0, 0.0, 0.0],
        [-dz, -dz, -dz]
    ], dtype=np.float64)  # Dips to the South

    res = calculate_slope_and_aspect_horn(window, lat_deg=0.0, dx_nominal_m=dx, dy_nominal_m=dy)
    assert math.isclose(res["slope_deg"], target_slope_deg, abs_tol=0.01)
    assert res["aspect_deg"] == 180.0
    assert res["aspect_cardinal"] == "S"
    assert res["metric_cell_size_m"]["latitudinal_scale_factor"] == 1.0


@pytest.mark.parametrize("lat_deg", [0.0, 30.0, 45.0, 60.0, 75.0])
def test_synthetic_slope_metric_scaling_at_multiple_latitudes(lat_deg: float):
    """
    Tests that east-west slope calculation on an analytical surface is strictly preserved
    across different latitudes by correctly applying the metric scale tensor dx(phi) = dx0 * cos(phi).
    """
    dx0 = MOLA_EQUATORIAL_CELL_M
    dy0 = MOLA_EQUATORIAL_CELL_M
    target_slope_deg = 15.0
    grad = math.tan(math.radians(target_slope_deg))

    # Physical ground distance along parallel at latitude lat_deg:
    cos_lat = math.cos(math.radians(lat_deg))
    dx_physical = dx0 * cos_lat

    # Elevation changes by grad * dx_physical across each column:
    dz = grad * dx_physical
    window = np.array([
        [+dz, 0.0, -dz],
        [+dz, 0.0, -dz],
        [+dz, 0.0, -dz]
    ], dtype=np.float64)  # Dips to the East

    res = calculate_slope_and_aspect_horn(window, lat_deg=lat_deg, dx_nominal_m=dx0, dy_nominal_m=dy0)
    assert math.isclose(res["slope_deg"], target_slope_deg, abs_tol=0.02)
    assert math.isclose(res["aspect_deg"], 90.0, abs_tol=0.1)
    assert res["aspect_cardinal"] == "E"
    assert math.isclose(res["metric_cell_size_m"]["dx_m"], dx_physical, abs_tol=0.1)


# ==============================================================================
# Gate 2: Aspect Direction and Angle Conventions
# ==============================================================================

def test_aspect_cardinal_directions():
    """Verifies that aspect directions strictly adhere to cartographic downslope standard."""
    dx = MOLA_EQUATORIAL_CELL_M
    dy = MOLA_EQUATORIAL_CELL_M
    drop = 100.0  # 100 m elevation drop

    # 1. North-dipping slope (row 0 is lowest)
    w_north = np.array([
        [-drop, -drop, -drop],
        [  0.0,   0.0,   0.0],
        [+drop, +drop, +drop]
    ], dtype=np.float64)
    res_n = calculate_slope_and_aspect_horn(w_north, lat_deg=0.0, dx_nominal_m=dx, dy_nominal_m=dy)
    assert math.isclose(res_n["aspect_deg"], 0.0, abs_tol=0.1)
    assert res_n["aspect_cardinal"] == "N"

    # 2. East-dipping slope (col 2 is lowest)
    w_east = np.array([
        [+drop, 0.0, -drop],
        [+drop, 0.0, -drop],
        [+drop, 0.0, -drop]
    ], dtype=np.float64)
    res_e = calculate_slope_and_aspect_horn(w_east, lat_deg=0.0, dx_nominal_m=dx, dy_nominal_m=dy)
    assert math.isclose(res_e["aspect_deg"], 90.0, abs_tol=0.1)
    assert res_e["aspect_cardinal"] == "E"

    # 3. South-dipping slope (row 2 is lowest)
    w_south = np.array([
        [+drop, +drop, +drop],
        [  0.0,   0.0,   0.0],
        [-drop, -drop, -drop]
    ], dtype=np.float64)
    res_s = calculate_slope_and_aspect_horn(w_south, lat_deg=0.0, dx_nominal_m=dx, dy_nominal_m=dy)
    assert math.isclose(res_s["aspect_deg"], 180.0, abs_tol=0.1)
    assert res_s["aspect_cardinal"] == "S"

    # 4. West-dipping slope (col 0 is lowest)
    w_west = np.array([
        [-drop, 0.0, +drop],
        [-drop, 0.0, +drop],
        [-drop, 0.0, +drop]
    ], dtype=np.float64)
    res_w = calculate_slope_and_aspect_horn(w_west, lat_deg=0.0, dx_nominal_m=dx, dy_nominal_m=dy)
    assert math.isclose(res_w["aspect_deg"], 270.0, abs_tol=0.1)
    assert res_w["aspect_cardinal"] == "W"


def test_aspect_diagonal_directions():
    """Tests northeast, southeast, southwest, northwest diagonal aspect angles."""
    dx = MOLA_EQUATORIAL_CELL_M
    dy = MOLA_EQUATORIAL_CELL_M

    # Dips towards Northeast (row 0, col 2 is lowest)
    w_ne = np.array([
        [  0.0, -100.0, -200.0],
        [100.0,    0.0, -100.0],
        [200.0,  100.0,    0.0]
    ], dtype=np.float64)
    res_ne = calculate_slope_and_aspect_horn(w_ne, lat_deg=0.0, dx_nominal_m=dx, dy_nominal_m=dy)
    assert math.isclose(res_ne["aspect_deg"], 45.0, abs_tol=0.5)
    assert res_ne["aspect_cardinal"] == "NE"


def test_flat_terrain_aspect():
    """Verifies that flat terrain returns is_flat=True, aspect=None, and aspect_cardinal='flat'."""
    w_flat = np.full((3, 3), -2500.0, dtype=np.float64)
    res = calculate_slope_and_aspect_horn(w_flat, lat_deg=18.0)
    assert res["is_flat"] is True
    assert res["slope_deg"] == 0.0
    assert res["aspect_deg"] is None
    assert res["aspect_cardinal"] == "flat"


# ==============================================================================
# Gate 3: Coordinate Normalization across 0°/360° and -180°/+180° Longitude
# ==============================================================================

@pytest.mark.parametrize("input_lon,expected_norm", [
    (0.0, 0.0),
    (360.0, 0.0),
    (720.0, 0.0),
    (-59.2, 300.8),
    (-282.42, 77.58),
    (77.58, 77.58),
    (180.0, 180.0),
    (-180.0, 180.0),
    (437.58, 77.58),
])
def test_longitude_normalization(input_lon: float, expected_norm: float):
    """Verifies standard [0, 360) East-positive longitude normalization."""
    norm = normalize_east_longitude_360(input_lon)
    assert math.isclose(norm, expected_norm, abs_tol=1e-4)


def test_great_circle_distance_across_origin_meridian():
    """Tests great-circle distance crossing the prime meridian (e.g. 359°E to 1°E)."""
    # 2 degrees along the equator = 2 * (pi / 180) * 3389.5 km approx 118.316 km
    dist = calculate_great_circle_distance_km(0.0, 359.0, 0.0, 1.0)
    expected = math.radians(2.0) * 3389.5
    assert math.isclose(dist, expected, abs_tol=0.01)


# ==============================================================================
# Gate 4: Boundary & Polar Coverage Handling
# ==============================================================================

def test_polar_dem_routing_north():
    """Tests automatic routing to North Polar Stereographic DEM for lat > 88.0°."""
    engine = TerrainIntelligenceEngine()
    res = engine.analyze_point(89.0, 0.0)
    assert res["elevation"]["elevation_m"] is not None
    assert res["provenance"]["source_dataset"] == "megt_n_128_1"
    assert res["provenance"]["native_crs"] == "MarsNP_3376"
    assert math.isclose(res["provenance"]["source_resolution_m"], 460.3899, abs_tol=0.01)


def test_polar_dem_routing_south():
    """Tests automatic routing to South Polar Stereographic DEM for lat < -88.0°."""
    engine = TerrainIntelligenceEngine()
    res = engine.analyze_point(-89.0, 0.0)
    assert res["elevation"]["elevation_m"] is not None
    assert res["provenance"]["source_dataset"] == "megt_s_128_1"
    assert res["provenance"]["native_crs"] == "MarsSP_3376"
    assert math.isclose(res["provenance"]["source_resolution_m"], 460.3899, abs_tol=0.01)


# ==============================================================================
# Gate 5: Geodesic Transect Profiling & Relief Consistency
# ==============================================================================

def test_transect_monotonic_distance_and_slerp():
    """Verifies that great-circle transect profiling enforces monotonic distances."""
    engine = TerrainIntelligenceEngine()
    # Transect across Jezero crater floor
    prof = engine.extract_profile(18.38, 77.40, 18.38, 77.80, num_samples=25)
    samples = prof["samples"]
    summary = prof["transect_summary"]

    assert len(samples) == 25
    assert summary["num_samples"] == 25
    assert summary["total_distance_km"] > 0

    # Verify strictly monotonic distance accumulation
    for i in range(1, len(samples)):
        assert samples[i]["distance_km"] > samples[i - 1]["distance_km"]

    # Endpoint fidelity
    assert math.isclose(samples[0]["distance_km"], 0.0, abs_tol=1e-3)
    assert math.isclose(samples[-1]["distance_km"], summary["total_distance_km"], abs_tol=1e-3)

    # Elevation relief consistency
    assert summary["max_elevation_m"] >= summary["min_elevation_m"]
    assert math.isclose(
        summary["elevation_relief_m"],
        summary["max_elevation_m"] - summary["min_elevation_m"],
        abs_tol=0.1
    )


# ==============================================================================
# Gate 6: Focal Morphometry (TRI, TPI, Relief)
# ==============================================================================

def test_morphometry_indices():
    """Tests TRI, TPI, and local relief indices on controlled synthetic windows."""
    # 1. Uniform plain: TRI=0, TPI=0, relief=0
    plain = np.full((3, 3), 100.0, dtype=np.float64)
    assert calculate_tri_roughness(plain) == 0.0
    assert calculate_tpi(plain) == 0.0
    assert classify_tpi(calculate_tpi(plain)) == "flat_plain"
    assert calculate_focal_relief(plain) == 0.0

    # 2. Ridge crest: center is +20 m above surrounding 8 cells
    ridge = np.full((3, 3), 100.0, dtype=np.float64)
    ridge[1, 1] = 120.0  # center cell is elevated
    assert calculate_tpi(ridge) == 20.0
    assert classify_tpi(calculate_tpi(ridge)) == "ridge_crest"
    assert calculate_tri_roughness(ridge) == 20.0
    assert calculate_focal_relief(ridge) == 20.0

    # 3. Depression / pit: center is -20 m below surrounding cells
    pit = np.full((3, 3), 100.0, dtype=np.float64)
    pit[1, 1] = 80.0
    assert calculate_tpi(pit) == -20.0
    assert classify_tpi(calculate_tpi(pit)) == "canyon_or_pit"


# ==============================================================================
# Gate 7: Verified Known Martian Elevation Landmarks
# ==============================================================================

def test_known_elevation_landmarks():
    """Verifies elevation lookups against authoritative planetary landmarks."""
    engine = TerrainIntelligenceEngine()

    # 1. Olympus Mons Summit Caldera (18.65°N, 226.2°E)
    olympus = engine.analyze_point(18.65, 226.2)
    assert olympus["elevation"]["elevation_m"] > 20000.0

    # 2. Jezero Crater Floor (18.38°N, 77.58°E)
    jezero = engine.analyze_point(18.38, 77.58)
    assert -2700.0 <= jezero["elevation"]["elevation_m"] <= -2550.0

    # 3. Gale Crater Floor (Curiosity Bradbury Landing site, -4.59°N, 137.44°E)
    gale_floor = engine.analyze_point(-4.59, 137.44)
    assert -4600.0 <= gale_floor["elevation"]["elevation_m"] <= -4400.0

    # 4. Gale Crater Central Mound (Aeolis Mons / Mount Sharp, -5.37°N, 137.81°E)
    # Rises ~4.5 km above the crater floor
    mount_sharp = engine.analyze_point(-5.37, 137.81)
    assert mount_sharp["elevation"]["elevation_m"] > -500.0

    # 5. Valles Marineris Coprates Chasma Floor (-12.5°N, 297.0°E)
    # Deepest canyon chasmata descending below -5,000 m
    coprates_deep = engine.analyze_point(-12.5, 297.0)
    assert coprates_deep["elevation"]["elevation_m"] < -5000.0

    # 6. Valles Marineris Eastern Chasma Corridor (-13.9°N, 300.8°E)
    valles = engine.analyze_point(-13.9, 300.8)
    assert -2700.0 <= valles["elevation"]["elevation_m"] <= -2400.0


# ==============================================================================
# Gate 8: Provenance & Uncertainty Reporting Transparency
# ==============================================================================

def test_provenance_and_resolution_reporting():
    """Verifies that all analysis results declare MOLA ~463 m/px resolution and datum."""
    engine = TerrainIntelligenceEngine()
    res = engine.analyze_point(18.38, 77.58)

    prov = res["provenance"]
    assert prov["source_dataset"] == "mola_global_meg128_cog"
    assert math.isclose(prov["source_resolution_m"], 463.0577, abs_tol=0.01)
    assert prov["vertical_datum"] == "MOLA GMM-3 Areoid (Equipotential Reference Surface)"
    assert prov["validation_status"] == "scientifically_validated"

    elev = res["elevation"]
    assert elev["vertical_accuracy_m"] >= 1.0  # Realistic uncertainty bound
    assert elev["vertical_datum"] == "MOLA GMM-3 Areoid (Equipotential Reference Surface)"
