"""
Terrain analysis endpoints.
Provides endpoints for point analysis, great-circle transect profiles, morphometric statistics,
and comparative site analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from zuhura.schemas.terrain import (
    PointAnalysisRequest,
    PointAnalysisResponse,
    TerrainProfileRequest,
    TerrainProfileResponse,
    TerrainStatisticsRequest,
    TerrainStatisticsResponse,
    TerrainCompareRequest,
    TerrainCompareResponse,
)
from zuhura.terrain_intelligence.engine import (
    TerrainIntelligenceEngine,
    get_terrain_engine,
)

router = APIRouter()


@router.post(
    "/point-analysis",
    response_model=PointAnalysisResponse,
    summary="Mars Surface Point Terrain Analysis",
    description=(
        "Computes instantaneous elevation, metric latitude-scaled slope, aspect azimuth, "
        "and focal morphometry (TRI/TPI) using the validated MOLA global DEM."
    ),
    status_code=status.HTTP_200_OK,
)
async def analyze_terrain_point(
    req: PointAnalysisRequest,
    engine: TerrainIntelligenceEngine = Depends(get_terrain_engine),
) -> PointAnalysisResponse:
    try:
        result = engine.analyze_point(
            lat=req.latitude,
            lon=req.longitude,
            kernel_size=req.kernel_size,
            include_morphometry=req.include_morphometry,
        )
        return PointAnalysisResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Global MOLA elevation dataset temporarily unavailable.",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terrain analysis computation failed: {str(e)}",
        ) from e


@router.post(
    "/profile",
    response_model=TerrainProfileResponse,
    summary="Great-Circle Geodesic Transect Profile",
    description=(
        "Generates an elevation profile along a great-circle geodesic between two coordinates "
        "using spherical linear interpolation (Slerp) and sub-pixel bilinear elevation sampling."
    ),
    status_code=status.HTTP_200_OK,
)
async def extract_transect_profile(
    req: TerrainProfileRequest,
    engine: TerrainIntelligenceEngine = Depends(get_terrain_engine),
) -> TerrainProfileResponse:
    try:
        result = engine.extract_profile(
            start_lat=req.start_point.latitude,
            start_lon=req.start_point.longitude,
            end_lat=req.end_point.latitude,
            end_lon=req.end_point.longitude,
            num_samples=req.num_samples,
            include_derivatives=req.include_derivatives,
        )
        return TerrainProfileResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Global MOLA elevation dataset temporarily unavailable.",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transect profile extraction failed: {str(e)}",
        ) from e


@router.post(
    "/statistics",
    response_model=TerrainStatisticsResponse,
    summary="Local Morphometric Statistics Footprint",
    description=(
        "Extracts statistical distributions of elevation, slopes, trafficability grade, "
        "and roughness indices across a circular geographic footprint on Mars."
    ),
    status_code=status.HTTP_200_OK,
)
async def calculate_area_statistics(
    req: TerrainStatisticsRequest,
    engine: TerrainIntelligenceEngine = Depends(get_terrain_engine),
) -> TerrainStatisticsResponse:
    try:
        result = engine.compute_area_statistics(
            lat=req.center_point.latitude,
            lon=req.center_point.longitude,
            radius_km=req.radius_km,
        )
        return TerrainStatisticsResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Global MOLA elevation dataset temporarily unavailable.",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Area statistics calculation failed: {str(e)}",
        ) from e


@router.post(
    "/compare",
    response_model=TerrainCompareResponse,
    summary="Head-to-Head Spatial Terrain Comparison",
    description=(
        "Compares two candidate surface investigation sites, reporting separation distance, "
        "net elevation change, gradient percentage, and side-by-side morphometric metrics."
    ),
    status_code=status.HTTP_200_OK,
)
async def compare_terrain_locations(
    req: TerrainCompareRequest,
    engine: TerrainIntelligenceEngine = Depends(get_terrain_engine),
) -> TerrainCompareResponse:
    try:
        result = engine.compare_locations(
            lat_a=req.site_a.latitude,
            lon_a=req.site_a.longitude,
            lat_b=req.site_b.latitude,
            lon_b=req.site_b.longitude,
            name_a=req.name_a or "Site A",
            name_b=req.name_b or "Site B",
        )
        return TerrainCompareResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Global MOLA elevation dataset temporarily unavailable.",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Site comparison computation failed: {str(e)}",
        ) from e
