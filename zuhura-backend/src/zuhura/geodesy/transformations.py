import math
from typing import Tuple
from zuhura.geodesy.constants import (
    MARS_A_EQUATORIAL_RADIUS_M,
    MARS_C_POLAR_RADIUS_M,
    MARS_FLATTENING,
    MARS_E_SQUARED,
    MARS_MEAN_RADIUS_M,
)


def planetographic_to_planetocentric_lat(lat_deg: float) -> float:
    """
    Converts Mars Planetographic latitude (phi_g) to Planetocentric latitude (phi_c) in degrees.
    Formula: tan(phi_c) = (1 - f)^2 * tan(phi_g) = (C / A)^2 * tan(phi_g)
    """
    if abs(lat_deg) >= 90.0:
        return 90.0 if lat_deg > 0 else -90.0
    if lat_deg == 0.0:
        return 0.0

    phi_g_rad = math.radians(lat_deg)
    ratio_sq = (MARS_C_POLAR_RADIUS_M / MARS_A_EQUATORIAL_RADIUS_M) ** 2
    phi_c_rad = math.atan(ratio_sq * math.tan(phi_g_rad))
    return math.degrees(phi_c_rad)


def planetocentric_to_planetographic_lat(lat_deg: float) -> float:
    """
    Converts Mars Planetocentric latitude (phi_c) to Planetographic latitude (phi_g) in degrees.
    Formula: tan(phi_g) = tan(phi_c) / (1 - f)^2 = (A / C)^2 * tan(phi_c)
    """
    if abs(lat_deg) >= 90.0:
        return 90.0 if lat_deg > 0 else -90.0
    if lat_deg == 0.0:
        return 0.0

    phi_c_rad = math.radians(lat_deg)
    inv_ratio_sq = (MARS_A_EQUATORIAL_RADIUS_M / MARS_C_POLAR_RADIUS_M) ** 2
    phi_g_rad = math.atan(inv_ratio_sq * math.tan(phi_c_rad))
    return math.degrees(phi_g_rad)


def normalize_east_longitude(
    lon_deg: float, is_west_positive: bool = False, range_180: bool = False
) -> float:
    """
    Normalizes Martian longitude to standard East-positive convention.
    Can return in [0, 360) or [-180, +180) range.
    """
    lon = float(lon_deg)
    if is_west_positive:
        lon = (360.0 - lon) % 360.0

    # Normalize to [0, 360)
    lon = lon % 360.0
    if lon < 0.0:
        lon += 360.0

    if range_180:
        if lon > 180.0:
            lon -= 360.0

    return lon


def calculate_latitudinal_positional_difference_km(lat_deg: float) -> float:
    """
    Calculates the spatial distance on the Martian surface between
    the same numerical latitude under planetographic vs planetocentric definitions.
    Demonstrates the ~20.4 km maximum discrepancy around 45° latitude.
    """
    phi_c = planetographic_to_planetocentric_lat(lat_deg)
    delta_deg = abs(lat_deg - phi_c)
    delta_rad = math.radians(delta_deg)
    return delta_rad * MARS_MEAN_RADIUS_M / 1000.0


def planetocentric_to_cartesian(
    lat_deg: float, lon_deg: float, alt_m: float = 0.0
) -> Tuple[float, float, float]:
    """
    Converts Mars planetocentric (lat, lon, altitude) to 3D Cartesian coordinates (X, Y, Z).
    """
    lat_rad = math.radians(lat_deg)
    lon_rad = math.radians(normalize_east_longitude(lon_deg))

    # Radius of ellipsoid at planetocentric latitude
    cos_lat = math.cos(lat_rad)
    sin_lat = math.sin(lat_rad)
    a = MARS_A_EQUATORIAL_RADIUS_M
    c = MARS_C_POLAR_RADIUS_M

    # Ellipsoidal radius r(phi)
    r = (a * c) / math.sqrt((c * cos_lat) ** 2 + (a * sin_lat) ** 2) + alt_m

    x = r * cos_lat * math.cos(lon_rad)
    y = r * cos_lat * math.sin(lon_rad)
    z = r * sin_lat
    return (x, y, z)


def cartesian_to_planetocentric(
    x: float, y: float, z: float
) -> Tuple[float, float, float]:
    """
    Converts 3D Cartesian coordinates (X, Y, Z) to Mars Planetocentric (lat_deg, lon_deg, alt_m).
    """
    xy_dist = math.sqrt(x**2 + y**2)
    lon_rad = math.atan2(y, x)
    lat_rad = math.atan2(z, xy_dist)

    lon_deg = normalize_east_longitude(math.degrees(lon_rad))
    lat_deg = math.degrees(lat_rad)

    # Reference ellipsoidal radius at this latitude
    cos_lat = math.cos(lat_rad)
    sin_lat = math.sin(lat_rad)
    a = MARS_A_EQUATORIAL_RADIUS_M
    c = MARS_C_POLAR_RADIUS_M
    r_ellip = (a * c) / math.sqrt((c * cos_lat) ** 2 + (a * sin_lat) ** 2)

    total_r = math.sqrt(x**2 + y**2 + z**2)
    alt_m = total_r - r_ellip

    return (lat_deg, lon_deg, alt_m)


def mars_surface_distance_km(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Great-circle spherical distance on Mars using Mean Volumetric Radius (3389.5 km).
    """
    phi1, lambda1 = math.radians(lat1), math.radians(lon1)
    phi2, lambda2 = math.radians(lat2), math.radians(lon2)

    dphi = phi2 - phi1
    dlambda = lambda2 - lambda1

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return (MARS_MEAN_RADIUS_M * c) / 1000.0
