"""
Solar illumination and hillshade endpoints.
Computes solar illumination vectors, solar azimuth and elevation, and sun direction
vectors for dynamic terrain lighting in CesiumJS and 3D planetary rendering.

Differentiates explicitly between:
1. Physical Solar Geometry (derived from Martian solar longitude Ls and solar hour angle)
2. Interactive / Artistic Illumination (user-specified azimuth and elevation angles)
"""

import math
from typing import Dict, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from zuhura_data.terrain.quantized_mesh import MARS_A, MARS_C

router = APIRouter()

# Mars Orbital and Rotational Constants
MARS_OBLIQUITY_DEG = 25.19  # Axial tilt relative to orbital plane


class SolarPositionResponse(BaseModel):
    latitude: float = Field(..., description="Target planetocentric latitude in degrees")
    longitude: float = Field(..., description="Target East-positive longitude in degrees")
    mode: str = Field(..., description="Calculation mode: 'solar_ephemeris_model' or 'interactive_visualization'")
    solar_azimuth_deg: float = Field(..., description="Sun azimuth angle from North clockwise [0, 360) degrees")
    solar_elevation_deg: float = Field(..., description="Sun elevation angle above local horizon [-90, +90] degrees")
    sun_direction_mcmf: list[float] = Field(..., description="Normalized unit vector [X, Y, Z] pointing toward Sun in MCMF frame")
    sun_direction_enu: list[float] = Field(..., description="Normalized unit vector [East, North, Up] in local tangent frame")
    is_illuminated: bool = Field(..., description="True if sun is above the local geometric horizon")
    solar_longitude_ls: Optional[float] = Field(None, description="Martian solar longitude Ls in degrees [0, 360)")
    local_solar_time_hours: Optional[float] = Field(None, description="Local Martian true solar time in decimal hours [0, 24)")
    scientific_disclaimer: str = Field(..., description="Attribution and physical validity disclaimer")


@router.get("/solar-position", response_model=SolarPositionResponse, summary="Compute Martian Solar Illumination Geometry")
async def get_solar_position(
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Observer planetocentric latitude in degrees"),
    longitude: float = Query(..., description="Observer East-positive longitude in degrees"),
    solar_longitude_ls: Optional[float] = Query(None, ge=0.0, le=360.0, description="Martian solar longitude Ls (season) in degrees"),
    solar_time_hours: Optional[float] = Query(None, ge=0.0, le=24.0, description="Local Martian true solar time in decimal hours [0, 24)"),
    azimuth_override: Optional[float] = Query(None, ge=0.0, le=360.0, description="Manual solar azimuth angle [0, 360) for interactive visualization"),
    elevation_override: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Manual solar elevation angle [-90, 90] for interactive visualization")
):
    """
    Computes solar azimuth, elevation, and 3D direction vectors for dynamic terrain illumination.
    Supports physical ephemeris geometry (via Ls and solar time) or interactive lighting overrides.
    """
    # Normalize longitude to [0, 360)
    lon360 = longitude % 360.0
    if lon360 < 0:
        lon360 += 360.0

    phi = math.radians(latitude)
    lam = math.radians(lon360)

    if azimuth_override is not None and elevation_override is not None:
        # Interactive / Artistic Mode
        mode = "interactive_visualization"
        azimuth_deg = azimuth_override % 360.0
        elevation_deg = elevation_override
        disclaimer = (
            "Interactive visualization mode: Solar illumination parameters are user-controlled "
            "for visual relief enhancement and morphology inspection. Not a physical ephemeris measurement."
        )
    elif solar_longitude_ls is not None and solar_time_hours is not None:
        # Physical Solar Ephemeris Approximation
        mode = "solar_ephemeris_model"
        ls_rad = math.radians(solar_longitude_ls)
        # Solar declination on Mars: delta = arcsin(sin(obliquity) * sin(Ls))
        obliq_rad = math.radians(MARS_OBLIQUITY_DEG)
        sin_delta = math.sin(obliq_rad) * math.sin(ls_rad)
        delta_rad = math.asin(sin_delta)
        cos_delta = math.cos(delta_rad)

        # Hour angle: H = (t_solar - 12.0) * 15 degrees
        hour_angle_deg = (solar_time_hours - 12.0) * 15.0
        h_rad = math.radians(hour_angle_deg)

        # Solar elevation angle: sin(elev) = sin(phi)*sin(delta) + cos(phi)*cos(delta)*cos(H)
        sin_elev = math.sin(phi) * sin_delta + math.cos(phi) * cos_delta * math.cos(h_rad)
        elevation_rad = math.asin(max(-1.0, min(1.0, sin_elev)))
        elevation_deg = math.degrees(elevation_rad)

        # Solar azimuth angle: tan(A) = sin(H) / (cos(H)*sin(phi) - tan(delta)*cos(phi))
        denom = math.cos(h_rad) * math.sin(phi) - math.tan(delta_rad) * math.cos(phi)
        az_rad = math.atan2(math.sin(h_rad), denom)
        azimuth_deg = (math.degrees(az_rad) + 180.0) % 360.0

        disclaimer = (
            f"Physical solar ephemeris model: Computed for Mars solar longitude Ls={solar_longitude_ls:.1f} deg "
            f"and local solar time={solar_time_hours:.2f} hrs using standard IAU axial obliquity 25.19 deg."
        )
    else:
        # Default standard afternoon sun (Azimuth 315 NW, Elevation 45)
        mode = "interactive_visualization"
        azimuth_deg = 315.0
        elevation_deg = 45.0
        disclaimer = "Default Mars terrain hillshade illumination (Azimuth 315 deg, Elevation 45 deg)."

    # Compute Local Tangent (ENU: East, North, Up) unit vector
    el_rad = math.radians(elevation_deg)
    az_rad = math.radians(azimuth_deg)

    # In ENU:
    # East = sin(azimuth) * cos(elevation)
    # North = cos(azimuth) * cos(elevation)
    # Up = sin(elevation)
    e_enu = math.sin(az_rad) * math.cos(el_rad)
    n_enu = math.cos(az_rad) * math.cos(el_rad)
    u_enu = math.sin(el_rad)

    # Convert ENU to Mars-Centered Mars-Fixed (MCMF) Cartesian unit vector:
    # Transformation matrix from ENU to ECEF/MCMF:
    # X = -sin(lon)*E - sin(lat)*cos(lon)*N + cos(lat)*cos(lon)*U
    # Y =  cos(lon)*E - sin(lat)*sin(lon)*N + cos(lat)*sin(lon)*U
    # Z =  0*E        + cos(lat)*N          + sin(lat)*U
    x_mcmf = -math.sin(lam) * e_enu - math.sin(phi) * math.cos(lam) * n_enu + math.cos(phi) * math.cos(lam) * u_enu
    y_mcmf =  math.cos(lam) * e_enu - math.sin(phi) * math.sin(lam) * n_enu + math.cos(phi) * math.sin(lam) * u_enu
    z_mcmf =  math.cos(phi) * n_enu + math.sin(phi) * u_enu

    # Normalize
    mcmf_len = math.sqrt(x_mcmf**2 + y_mcmf**2 + z_mcmf**2)
    if mcmf_len > 0:
        sun_mcmf = [round(x_mcmf / mcmf_len, 6), round(y_mcmf / mcmf_len, 6), round(z_mcmf / mcmf_len, 6)]
    else:
        sun_mcmf = [0.0, 0.0, 1.0]

    return SolarPositionResponse(
        latitude=latitude,
        longitude=lon360,
        mode=mode,
        solar_azimuth_deg=round(azimuth_deg, 2),
        solar_elevation_deg=round(elevation_deg, 2),
        sun_direction_mcmf=sun_mcmf,
        sun_direction_enu=[round(e_enu, 6), round(n_enu, 6), round(u_enu, 6)],
        is_illuminated=(elevation_deg > 0.0),
        solar_longitude_ls=solar_longitude_ls,
        local_solar_time_hours=solar_time_hours,
        scientific_disclaimer=disclaimer
    )
