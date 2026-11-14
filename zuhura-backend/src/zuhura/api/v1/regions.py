"""
Region discovery endpoints.
Provides endpoints for terrain segmentation, polygon boundary extraction,
and GeoJSON export.
"""

from fastapi import APIRouter, HTTPException, status
from zuhura.segmentation.engine import (
    RegionDiscoveryEngine,
    RegionDiscoveryRequest,
    RegionDiscoveryResponse,
    GeologicalRegion,
)

router = APIRouter()
_discovery_engine = RegionDiscoveryEngine()


@router.post(
    "/discover",
    response_model=RegionDiscoveryResponse,
    summary="Discover Candidate Geological Regions from Terrain Clustering",
    description=(
        "Analyzes regional topography, slope variance, and terrain roughness to segment candidate "
        "geological units, generating closed polygon boundaries and descriptive provisional names."
    ),
    status_code=status.HTTP_200_OK,
)
async def discover_geological_regions(req: RegionDiscoveryRequest) -> RegionDiscoveryResponse:
    try:
        return _discovery_engine.discover_regions(req)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Geological region segmentation failed: {str(e)}",
        ) from e


@router.get(
    "/presets",
    summary="List Pre-segmented Reference Geological Regions",
    description="Returns pre-computed geological unit boundaries for major Mars science exploration zones.",
)
async def get_preset_regions():
    # Pre-computed preset regions for Jezero Crater Western Delta
    req = RegionDiscoveryRequest(
        center_latitude=18.38,
        center_longitude=77.58,
        search_radius_km=60.0,
    )
    return _discovery_engine.discover_regions(req)
