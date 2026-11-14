"""
Location details shown when hovering over the globe.
Provides cached location details for cursor hover and tap events.
"""

import json
import logging
import math
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from functools import lru_cache
from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field

from zuhura.core.config import settings
from zuhura.geodesy.transformations import (
    normalize_east_longitude,
    planetocentric_to_planetographic_lat,
    mars_surface_distance_km,
)
from zuhura.terrain_intelligence.engine import get_terrain_engine
from zuhura.api.v1.spatial import MARS_FEATURES, estimate_mars_elevation

router = APIRouter()
logger = logging.getLogger(__name__)

# Load expanded 78 IAU features and 18 regional provinces
EXPANDED_FEATURES: List[Dict[str, Any]] = list(MARS_FEATURES)
EXPANDED_REGIONS: List[Dict[str, Any]] = []

try:
    data_dir = Path(settings.DATA_REPO_ROOT) / "data"
    f_path = data_dir / "mars_features.json"
    r_path = data_dir / "mars_regions.json"
    if f_path.exists():
        raw_feats = json.loads(f_path.read_text())
        for rf in raw_feats:
            EXPANDED_FEATURES.append({
                "id": rf.get("id"),
                "name": rf.get("name"),
                "type": rf.get("category") or rf.get("type") or "crater",
                "latitude": float(rf.get("lat") or 0.0),
                "longitude": float(rf.get("lon") or 0.0),
                "diameter_km": float(rf.get("diameter_km") or 0.0),
                "elevation_m": float(rf.get("elevation_m") or 0.0),
                "description": rf.get("description", "Martian geographical feature.")
            })
    if r_path.exists():
        EXPANDED_REGIONS = json.loads(r_path.read_text())
except Exception:
    logger.warning("Optional Mars feature catalog failed to load", exc_info=True)


class NearbyFeatureInfo(BaseModel):
    name: str
    feature_type: str
    distance_km: float
    diameter_km: float
    is_inside: bool
    elevation_m: float
    description: str


class ImageryAvailability(BaseModel):
    viking_global_232m: bool = True
    ctx_regional_5m: bool = False
    hirise_local_submeter: bool = False
    themis_ir_100m: bool = False
    details: str


class HoverIntelligenceResponse(BaseModel):
    latitude: float
    longitude: float
    planetographic_latitude: float
    elevation_m: float
    vertical_datum: str = "Mars Areoid (MOLA GMM-3)"
    slope_degrees: float
    surface_description: str
    geological_era: str
    nearest_feature: Optional[NearbyFeatureInfo]
    imagery_coverage: ImageryAvailability
    solar_status: Dict[str, Any]
    data_source: str = "MOLA MEGDR 128 px/deg + IAU Planetary Nomenclature"


# Known regional bounding boxes for CTX / HiRISE footprints in catalog
JEZERO_BBOX = {"min_lat": 17.5, "max_lat": 19.5, "min_lon": 76.5, "max_lon": 78.5}
GALE_BBOX = {"min_lat": -6.0, "max_lat": -3.5, "min_lon": 136.5, "max_lon": 138.5}


def classify_geological_context(lat: float, lon: float, elev: float) -> Tuple[str, str]:
    """
    Determines likely geological era and terrain classification based on Mars dichotomy,
    elevation, and geographic latitude.
    """
    if elev > 10000.0:
        return "Amazonian Period (Volcanic)", "High-altitude volcanic construct / shield volcano edifice"
    elif elev < -4000.0:
        return "Noachian to Early Hesperian", "Deep impact basin or central crater floor with sedimentary infill"
    elif lat < 0.0 and elev > 0.0:
        return "Noachian Period (> 3.7 Ga)", "Heavily cratered Southern Highlands bedrock and ancient crustal plateaus"
    elif lat > 25.0 and elev < -2000.0:
        return "Hesperian to Amazonian", "Smooth Northern Lowlands plains (Vastitas Borealis), volcanic sheet flows or periglacial deposits"
    elif 17.0 <= lat <= 19.0 and 76.0 <= lon <= 79.0:
        return "Late Noachian / Early Hesperian", "Deltaic fan deposits within Jezero paleolake basin; clay-carbonate layered strata"
    else:
        return "Hesperian Transition Period", "Martian intermediate plains, intercrater ridged plains with aeolian mantle"


@lru_cache(maxsize=1024)
def _cached_hover_lookup(lat_rounded: float, lon_rounded: float) -> Dict[str, Any]:
    engine = get_terrain_engine()
    norm_lon = normalize_east_longitude(lon_rounded)
    lat = lat_rounded

    try:
        pt = engine.analyze_point(lat, norm_lon, kernel_size=3)
        elev = float(pt["elevation"]["elevation_m"])
        slope = float(pt["slope"]["slope_degrees"])
    except Exception:
        elev = float(estimate_mars_elevation(lat, norm_lon))
        slope = 2.0

    # Nearest IAU feature search
    nearest = None
    min_dist = float("inf")
    for f in EXPANDED_FEATURES:
        d = mars_surface_distance_km(lat, norm_lon, f["latitude"], f["longitude"])
        if d < min_dist:
            min_dist = d
            radius = (f.get("diameter_km", 10.0) / 2.0)
            nearest = {
                "name": f["name"],
                "feature_type": f.get("type", "crater"),
                "distance_km": round(d, 1),
                "diameter_km": float(f.get("diameter_km", 0.0)),
                "is_inside": d <= radius,
                "elevation_m": float(f.get("elevation_m", elev)),
                "description": f.get("description", "Planetary landmark.")
            }

    # Regional description check
    matched_region = None
    for r in EXPANDED_REGIONS:
        bounds = r.get("bounds", [])
        if bounds and len(bounds) >= 3:
            min_r_lon = min(b[0] for b in bounds)
            max_r_lon = max(b[0] for b in bounds)
            min_r_lat = min(b[1] for b in bounds)
            max_r_lat = max(b[1] for b in bounds)
            if min_r_lon <= norm_lon <= max_r_lon and min_r_lat <= lat <= max_r_lat:
                matched_region = r
                break

    era, desc = classify_geological_context(lat, norm_lon, elev)
    if nearest and nearest["distance_km"] <= max(25.0, nearest["diameter_km"] / 2.0 + 30.0):
        desc = f"{nearest['name']} — {nearest['description']}"
    elif matched_region:
        desc = f"{matched_region['name']} — {matched_region['description']} {matched_region.get('geology', '')}".strip()

    # Imagery coverage check
    in_jezero = (
        JEZERO_BBOX["min_lat"] <= lat <= JEZERO_BBOX["max_lat"]
        and JEZERO_BBOX["min_lon"] <= norm_lon <= JEZERO_BBOX["max_lon"]
    )
    in_gale = (
        GALE_BBOX["min_lat"] <= lat <= GALE_BBOX["max_lat"]
        and GALE_BBOX["min_lon"] <= norm_lon <= GALE_BBOX["max_lon"]
    )

    ctx_avail = in_jezero or in_gale
    hirise_avail = in_jezero
    themis_avail = in_jezero or in_gale or (abs(lat) < 60.0)

    imagery_info = {
        "viking_global_232m": True,
        "ctx_regional_5m": ctx_avail,
        "hirise_local_submeter": hirise_avail,
        "themis_ir_100m": themis_avail,
        "details": "Sub-meter HiRISE + 5m CTX mosaic available" if hirise_avail else (
            "Regional 5m CTX available" if ctx_avail else "Viking MDIM 2.1 (232 m/px) global basemap"
        )
    }

    era, desc = classify_geological_context(lat, norm_lon, elev)
    pg_lat = planetocentric_to_planetographic_lat(lat)

    # Solar illumination geometry approximation (noon Ls=0 baseline)
    phi = math.radians(lat)
    sol_elev_deg = math.degrees(math.asin(max(-1.0, min(1.0, math.cos(phi)))))
    is_day = sol_elev_deg > 0.0

    return {
        "latitude": lat,
        "longitude": norm_lon,
        "planetographic_latitude": round(pg_lat, 4),
        "elevation_m": round(elev, 1),
        "vertical_datum": "Mars Areoid (MOLA GMM-3)",
        "slope_degrees": round(slope, 1),
        "surface_description": desc,
        "geological_era": era,
        "nearest_feature": nearest if min_dist < 600.0 else None,
        "imagery_coverage": imagery_info,
        "solar_status": {
            "is_daylight": is_day,
            "solar_elevation_deg": round(sol_elev_deg, 1),
            "solar_azimuth_deg": 180.0
        },
        "data_source": "MGS MOLA MEGDR 128 px/deg + IAU Planetary Nomenclature Database"
    }


@router.get(
    "/inspect",
    response_model=HoverIntelligenceResponse,
    summary="Contextual Mars Geographic Information on Hover",
    description="Returns high-speed, cached terrain, geological era, nearest IAU features, and imagery footprint.",
)
async def hover_inspect_location(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Planetocentric latitude"),
    lon: float = Query(..., ge=-180.0, le=360.0, description="East-positive longitude"),
) -> HoverIntelligenceResponse:
    # Round to 3 decimal places (~59 meters on Mars) for effective spatial caching
    lat_r = round(lat, 3)
    lon_r = round(normalize_east_longitude(lon), 3)
    data = _cached_hover_lookup(lat_r, lon_r)
    return HoverIntelligenceResponse(**data)
