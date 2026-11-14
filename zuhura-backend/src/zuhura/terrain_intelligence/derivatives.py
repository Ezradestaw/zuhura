"""
Slope, aspect and curvature from elevation grids.
Implements the Metric Latitude-Scaled Horn (1981) finite-difference operator
for calculating slope and aspect on planetary digital elevation models.
"""

import math
from typing import Any, Dict, Optional
import numpy as np

# Nominal MOLA MEG128 cell dimension at Mars equator (1/128 degree on R=3,396,000 m sphere)
MOLA_EQUATORIAL_CELL_M: float = 463.0576672


def aspect_degrees_to_cardinal(aspect_deg: Optional[float]) -> str:
    """
    Converts aspect azimuth angle (0° to 360° clockwise from True North)
    to standard 8-point compass cardinal direction string.
    """
    if aspect_deg is None:
        return "flat"
    
    deg = aspect_deg % 360.0
    if 337.5 <= deg or deg < 22.5:
        return "N"
    elif 22.5 <= deg < 67.5:
        return "NE"
    elif 67.5 <= deg < 112.5:
        return "E"
    elif 112.5 <= deg < 157.5:
        return "SE"
    elif 157.5 <= deg < 202.5:
        return "S"
    elif 202.5 <= deg < 247.5:
        return "SW"
    elif 247.5 <= deg < 292.5:
        return "W"
    else:
        return "NW"


def calculate_slope_and_aspect_horn(
    window: np.ndarray,
    lat_deg: float,
    dx_nominal_m: float = MOLA_EQUATORIAL_CELL_M,
    dy_nominal_m: float = MOLA_EQUATORIAL_CELL_M
) -> Dict[str, Any]:
    """
    Calculates surface slope (in degrees) and aspect (in degrees clockwise from True North)
    using the Horn (1981) 3x3 finite-difference algorithm scaled by the local map-projection
    metric tensor at latitude lat_deg.

    Parameters:
        window: 2D numpy array of elevations (at least 3x3). Cast to float64 to prevent int16 overflow.
        lat_deg: Planetocentric latitude in degrees (-90 to +90).
        dx_nominal_m: Nominal cell width at equator (default 463.06 m).
        dy_nominal_m: Nominal cell height along meridian (default 463.06 m).

    Returns:
        Dict containing slope_deg, aspect_deg, aspect_cardinal, metric_cell_size_m, is_flat, and metadata.
    """
    arr = np.asarray(window, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[0] < 3 or arr.shape[1] < 3:
        raise ValueError(f"Input elevation window must be at least 3x3, got shape {arr.shape}")

    # Extract central 3x3 if window is larger
    if arr.shape != (3, 3):
        cy = arr.shape[0] // 2
        cx = arr.shape[1] // 2
        w3 = arr[cy - 1:cy + 2, cx - 1:cx + 2]
    else:
        w3 = arr

    # Metric latitude scaling for Simple Cylindrical projection:
    # Physical parallel cell width contracts as cos(phi): dx(phi) = dx0 * cos(phi)
    clamped_lat = max(-89.99, min(89.99, float(lat_deg)))
    lat_rad = math.radians(clamped_lat)
    cos_lat = math.cos(lat_rad)
    dx_m = dx_nominal_m * cos_lat
    dy_m = dy_nominal_m

    # Neighborhood indexing:
    # w3[0, :] = North row (top)
    # w3[1, :] = Center row
    # w3[2, :] = South row (bottom)
    # Col 0 = West, Col 1 = Center, Col 2 = East
    z_tl, z_t, z_tr = w3[0, 0], w3[0, 1], w3[0, 2]
    z_l,  z_c, z_r  = w3[1, 0], w3[1, 1], w3[1, 2]
    z_bl, z_b, z_br = w3[2, 0], w3[2, 1], w3[2, 2]

    # Weighted finite-difference partial derivatives (Horn, 1981)
    # dz/dx: East - West
    dz_dx = ((z_tr + 2.0 * z_r + z_br) - (z_tl + 2.0 * z_l + z_bl)) / (8.0 * dx_m)

    # dz/dy: North - South (in Cartesian space, North is +y, South is -y)
    # row 0 is North, row 2 is South, so (row 0 - row 2) is (z_north - z_south) = +dz/dy
    dz_dy = ((z_tl + 2.0 * z_t + z_tr) - (z_bl + 2.0 * z_b + z_br)) / (8.0 * dy_m)

    gradient_mag = math.sqrt(dz_dx**2 + dz_dy**2)
    slope_rad = math.atan(gradient_mag)
    slope_deg = math.degrees(slope_rad)

    # Flat threshold: slopes < 0.01 deg (~0.017% gradient)
    if slope_deg < 0.01 or gradient_mag < 1e-7:
        aspect_deg: Optional[float] = None
        aspect_cardinal = "flat"
        is_flat = True
    else:
        # Downslope direction vector:
        # As x increases (East), if dz/dx < 0, surface dips East -> u = -dz/dx > 0
        # As y increases (North), if dz/dy < 0, surface dips North -> v = -dz/dy > 0
        u = -dz_dx  # East component
        v = -dz_dy  # North component
        aspect_rad = math.atan2(u, v)
        aspect_deg = math.degrees(aspect_rad) % 360.0
        aspect_cardinal = aspect_degrees_to_cardinal(aspect_deg)
        is_flat = False

    return {
        "slope_deg": round(float(slope_deg), 2),
        "aspect_deg": round(float(aspect_deg), 1) if aspect_deg is not None else None,
        "aspect_cardinal": aspect_cardinal,
        "is_flat": is_flat,
        "partial_derivatives": {
            "dz_dx": float(dz_dx),
            "dz_dy": float(dz_dy),
            "gradient_magnitude": float(gradient_mag),
        },
        "metric_cell_size_m": {
            "dx_m": round(float(dx_m), 2),
            "dy_m": round(float(dy_m), 2),
            "latitudinal_scale_factor": round(float(cos_lat), 4),
        },
        "calculation_method": "Horn (1981) 3x3 weighted finite-difference with metric latitude scaling",
    }


def calculate_profile_curvature(
    window: np.ndarray,
    lat_deg: float,
    dx_nominal_m: float = MOLA_EQUATORIAL_CELL_M,
    dy_nominal_m: float = MOLA_EQUATORIAL_CELL_M
) -> float:
    """
    Calculates profile curvature (rate of slope change in the direction of steepest descent).
    Positive values indicate upwardly convex surfaces (accelerating flow);
    negative values indicate upwardly concave surfaces (decelerating flow).
    """
    arr = np.asarray(window, dtype=np.float64)
    if arr.shape != (3, 3):
        cy, cx = arr.shape[0] // 2, arr.shape[1] // 2
        w3 = arr[cy - 1:cy + 2, cx - 1:cx + 2]
    else:
        w3 = arr

    clamped_lat = max(-89.99, min(89.99, float(lat_deg)))
    dx = dx_nominal_m * math.cos(math.radians(clamped_lat))
    dy = dy_nominal_m

    z1, z2, z3 = w3[0, 0], w3[0, 1], w3[0, 2]
    z4, z5, z6 = w3[1, 0], w3[1, 1], w3[1, 2]
    z7, z8, z9 = w3[2, 0], w3[2, 1], w3[2, 2]

    # Partial derivative polynomial coefficients (Zevenbergen & Thorne, 1987)
    d = ((z4 + z6) / 2.0 - z5) / (dx**2)
    e = ((z2 + z8) / 2.0 - z5) / (dy**2)
    f = (-z1 + z3 + z7 - z9) / (4.0 * dx * dy)
    g = (-z4 + z6) / (2.0 * dx)
    h = (z2 - z8) / (2.0 * dy)

    denom = g**2 + h**2
    if denom < 1e-10:
        return 0.0

    curv = -2.0 * (d * g**2 + e * h**2 + f * g * h) / denom
    return round(float(curv * 100.0), 4)  # 1/100m units
