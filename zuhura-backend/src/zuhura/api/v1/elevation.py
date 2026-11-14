"""
Elevation API endpoints.
Provides zero-copy coordinate elevation lookups from MOLA Global COG (v3)
referenced to the MOLA GMM-3 areoid potential surface.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from zuhura.api.deps import get_science_access
from zuhura_data.access.client import ZuhuraScienceAccess
from zuhura_data.models.spatial import normalize_longitude_360

router = APIRouter()


@router.get("", summary="Get Mars Surface Elevation at Point")
@router.get("/", include_in_schema=False)
async def get_elevation_point(
    latitude: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Planetocentric latitude (-90 to +90)"),
    longitude: Optional[float] = Query(None, description="East-positive longitude in degrees"),
    lat: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Alias for latitude"),
    lon: Optional[float] = Query(None, description="Alias for longitude"),
    science_access: ZuhuraScienceAccess = Depends(get_science_access)
):
    """
    Returns verified Martian surface elevation in meters relative to the MOLA GMM-3 areoid.
    Uses zero-copy single-pixel window read from the global MOLA COG v3.
    """
    final_lat = latitude if latitude is not None else lat
    final_lon = longitude if longitude is not None else lon

    if final_lat is None or final_lon is None:
        raise HTTPException(
            status_code=400,
            detail="Missing coordinate parameters: provide 'latitude'/'longitude' or 'lat'/'lon'."
        )

    norm_lon = normalize_longitude_360(final_lon)

    # Outside MOLA global observation boundary (-88 to +88)
    if final_lat < -88.0 or final_lat > 88.0:
        return {
            "latitude": final_lat,
            "longitude": norm_lon,
            "elevation_m": None,
            "dataset_id": "zuhura-mola-global-v3-cog",
            "product_id": "mola_global_meg128_cog",
            "pixel_coordinates": None,
            "source_resolution_m": 463.0577,
            "native_crs": "Mars_simpCyl_c180 (IAU:49900 Sphere R=3396km)",
            "vertical_reference": "MOLA GMM-3 Areoid (Equipotential Reference Surface)",
            "nodata_status": True,
            "validation_status": "outside_coverage_boundary",
            "message": "Coordinate falls outside global MEG128 coverage (-88° to +88°). Consult polar DEM."
        }

    res = science_access.get_elevation_at_point(final_lat, norm_lon)
    if res.get("nodata_status"):
        return {
            "latitude": final_lat,
            "longitude": norm_lon,
            "elevation_m": None,
            "dataset_id": "zuhura-mola-global-v3-cog",
            "product_id": "mola_global_meg128_cog",
            "pixel_coordinates": res.get("pixel_coordinates"),
            "source_resolution_m": 463.0577,
            "native_crs": res.get("native_crs"),
            "vertical_reference": res.get("vertical_datum"),
            "nodata_status": True,
            "validation_status": "nodata"
        }

    return {
        "latitude": final_lat,
        "longitude": norm_lon,
        "elevation_m": res["elevation_m"],
        "dataset_id": "zuhura-mola-global-v3-cog",
        "product_id": "mola_global_meg128_cog",
        "pixel_coordinates": res.get("pixel_coordinates"),
        "source_resolution_m": 463.0577,
        "native_crs": res.get("native_crs"),
        "vertical_reference": res.get("vertical_datum"),
        "nodata_status": False,
        "validation_status": "scientifically_validated"
    }
