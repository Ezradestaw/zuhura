"""
Elevation profiles along geodesic transects.
Computes spherical linear interpolation (Slerp) along true Martian great-circle arcs
with monotonic cumulative distance accumulation and elevation relief statistics.
"""

import math
from typing import Any, Dict, List, Tuple
import numpy as np

# Mars Volumetric Mean Radius in meters (IAU 2015 standard)
MARS_MEAN_RADIUS_M: float = 3389500.0


def normalize_east_longitude_360(lon_deg: float) -> float:
    """Normalizes longitude into [0, 360) East-positive degrees."""
    norm = float(lon_deg) % 360.0
    return norm if norm >= 0.0 else norm + 360.0


def lat_lon_to_unit_vector(lat_deg: float, lon_deg: float) -> np.ndarray:
    """Converts planetocentric lat/lon into 3D unit vector on the sphere."""
    phi = math.radians(lat_deg)
    lam = math.radians(normalize_east_longitude_360(lon_deg))
    cos_phi = math.cos(phi)
    return np.array([
        cos_phi * math.cos(lam),
        cos_phi * math.sin(lam),
        math.sin(phi)
    ], dtype=np.float64)


def unit_vector_to_lat_lon(v: np.ndarray) -> Tuple[float, float]:
    """Converts 3D unit vector back to planetocentric (lat_deg, lon_deg)."""
    v_norm = v / np.linalg.norm(v)
    x, y, z = v_norm[0], v_norm[1], v_norm[2]
    phi_rad = math.asin(max(-1.0, min(1.0, z)))
    lam_rad = math.atan2(y, x)
    lat_deg = math.degrees(phi_rad)
    lon_deg = normalize_east_longitude_360(math.degrees(lam_rad))
    return lat_deg, lon_deg


def calculate_great_circle_distance_km(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Computes great-circle surface distance in km on Mars mean sphere."""
    v1 = lat_lon_to_unit_vector(lat1, lon1)
    v2 = lat_lon_to_unit_vector(lat2, lon2)
    dot = np.clip(np.dot(v1, v2), -1.0, 1.0)
    sigma = math.acos(dot)
    return (MARS_MEAN_RADIUS_M * sigma) / 1000.0


def interpolate_geodesic_transect(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    num_samples: int = 50
) -> List[Dict[str, float]]:
    """
    Interpolates num_samples along the great-circle arc from P1 to P2 using Slerp.
    Guarantees strictly monotonic distance accumulation from 0 to total_distance_km.
    """
    if num_samples < 2:
        raise ValueError(f"num_samples must be at least 2, got {num_samples}")

    v1 = lat_lon_to_unit_vector(lat1, lon1)
    v2 = lat_lon_to_unit_vector(lat2, lon2)

    dot = np.clip(np.dot(v1, v2), -1.0, 1.0)
    sigma = math.acos(dot)
    total_dist_km = (MARS_MEAN_RADIUS_M * sigma) / 1000.0

    stations: List[Dict[str, float]] = []

    # If start and end points are essentially identical
    if sigma < 1e-9:
        for i in range(num_samples):
            stations.append({
                "step": i,
                "fraction": round(i / (num_samples - 1), 4),
                "distance_km": 0.0,
                "latitude": round(lat1, 5),
                "longitude": round(normalize_east_longitude_360(lon1), 5),
            })
        return stations

    sin_sigma = math.sin(sigma)

    for i in range(num_samples):
        frac = i / (num_samples - 1)
        # Slerp formula: v(f) = (sin((1-f)*sigma)/sin(sigma))*v1 + (sin(f*sigma)/sin(sigma))*v2
        scale1 = math.sin((1.0 - frac) * sigma) / sin_sigma
        scale2 = math.sin(frac * sigma) / sin_sigma
        vf = scale1 * v1 + scale2 * v2
        lat_i, lon_i = unit_vector_to_lat_lon(vf)
        dist_i = frac * total_dist_km

        stations.append({
            "step": i,
            "fraction": round(frac, 4),
            "distance_km": round(dist_i, 3),
            "latitude": round(lat_i, 5),
            "longitude": round(lon_i, 5),
        })

    return stations


def compute_profile_summary(
    samples: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Computes aggregated terrain metrics from a sequence of elevation transect samples.
    """
    if not samples:
        return {}

    elevations = [s["elevation_m"] for s in samples if s.get("elevation_m") is not None]
    if not elevations:
        return {"error": "No valid elevation measurements in transect"}

    total_dist_km = float(samples[-1].get("distance_km", 0.0))
    n = len(elevations)
    min_elev = min(elevations)
    max_elev = max(elevations)
    mean_elev = sum(elevations) / n
    relief = max_elev - min_elev

    # Elevation gains and losses along transect
    gain_m = 0.0
    loss_m = 0.0
    slopes: List[float] = []

    for i in range(1, len(samples)):
        s_prev = samples[i - 1]
        s_curr = samples[i]
        z_prev = s_prev.get("elevation_m")
        z_curr = s_curr.get("elevation_m")
        d_prev = s_prev.get("distance_km", 0.0)
        d_curr = s_curr.get("distance_km", 0.0)

        if z_prev is not None and z_curr is not None:
            dz = z_curr - z_prev
            if dz > 0:
                gain_m += dz
            else:
                loss_m += abs(dz)

            # Segment slope in degrees
            ddist_m = (d_curr - d_prev) * 1000.0
            if ddist_m > 1e-3:
                seg_slope = math.degrees(math.atan(abs(dz) / ddist_m))
                slopes.append(seg_slope)

    mean_slope = sum(slopes) / len(slopes) if slopes else 0.0
    max_slope = max(slopes) if slopes else 0.0
    sample_step_m = (total_dist_km * 1000.0) / (n - 1) if n > 1 else 0.0

    return {
        "total_distance_km": round(total_dist_km, 3),
        "num_samples": n,
        "sample_step_m": round(sample_step_m, 1),
        "min_elevation_m": round(min_elev, 1),
        "max_elevation_m": round(max_elev, 1),
        "mean_elevation_m": round(mean_elev, 1),
        "elevation_relief_m": round(relief, 1),
        "cumulative_elevation_gain_m": round(gain_m, 1),
        "cumulative_elevation_loss_m": round(loss_m, 1),
        "mean_slope_deg": round(mean_slope, 2),
        "max_slope_deg": round(max_slope, 2),
    }
