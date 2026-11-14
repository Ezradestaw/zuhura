"""
Rover route planning and simulation endpoints.
Provides endpoints for routing, mobility constraint evaluation, multi-rover comparison,
Bekker terramechanics, diurnal insolation, and communications window calculations.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status

from zuhura.navigation.router import (
    NavigationRouter,
    RoutePlanningRequest,
    RoutePlanningResponse,
    MOBILITY_PROFILES,
    Waypoint,
)
from zuhura.navigation.mobility_model import (
    ROVER_SPECIFICATIONS,
    REGOLITH_DATABASE,
    RoverComparisonItem,
    CommunicationPass,
    calculate_comm_windows,
    simulate_multi_rover_comparison,
)
from zuhura.provenance.taxonomy import ProvenanceFactory, EpistemicClassification

router = APIRouter()
_nav_router = NavigationRouter()


class CommWindowsRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=360.0)


class MultiRoverSimulationRequest(BaseModel):
    start_latitude: float = Field(..., ge=-90.0, le=90.0)
    start_longitude: float = Field(..., ge=-180.0, le=360.0)
    destination_latitude: float = Field(..., ge=-90.0, le=90.0)
    destination_longitude: float = Field(..., ge=-180.0, le=360.0)
    rovers: Optional[List[str]] = Field(default=None, description="Subset of rovers to evaluate, or all registered if omitted")
    soil_type: str = Field(default="basaltic_sand", description="basaltic_sand, compact_dust, duricrust, bedrock, dune_fields")
    solar_longitude_ls: float = Field(default=180.0, ge=0.0, le=360.0, description="Mars season (0-360 deg)")
    dust_optical_depth_tau: float = Field(default=0.5, ge=0.05, le=5.0, description="Atmospheric dust opacity tau")


class MultiRoverSimulationResponse(BaseModel):
    status: str
    corridor_summary: Dict[str, Any]
    regolith_properties: Dict[str, Any]
    environmental_conditions: Dict[str, Any]
    comparison_results: List[RoverComparisonItem]
    scientific_provenance: Dict[str, Any]


@router.post(
    "/optimize-route",
    response_model=RoutePlanningResponse,
    summary="Optimize Terrain-Aware Traverse Route on Mars",
    description=(
        "Computes an A* pathfinding traverse between Martian coordinates accounting for MOLA elevation, "
        "metric slope penalties, terrain roughness, and rover mobility limits."
    ),
    status_code=status.HTTP_200_OK,
)
async def optimize_traverse_route(req: RoutePlanningRequest) -> RoutePlanningResponse:
    try:
        return _nav_router.calculate_routes(req)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Route optimization calculation failed: {str(e)}",
        ) from e


@router.get(
    "/profiles",
    summary="List Rover & Vehicle Mobility Profiles",
    description="Returns supported vehicle parameters, climbable slope limits, power sources, and mobility specifications.",
)
async def get_mobility_profiles():
    specs_dict = {k: v.model_dump() for k, v in ROVER_SPECIFICATIONS.items()}
    return {
        "status": "operational",
        "profiles": MOBILITY_PROFILES,
        "specifications": specs_dict,
        "count": len(ROVER_SPECIFICATIONS)
    }


@router.get(
    "/regolith-types",
    summary="List Martian Regolith Geotechnical Types",
    description="Returns Bekker-Wong soil mechanics parameters (cohesion, friction angle, sinkage moduli kc/kphi/n) for Martian soils.",
)
async def get_regolith_types():
    return {
        "status": "operational",
        "regolith_types": {k: v.model_dump() for k, v in REGOLITH_DATABASE.items()},
        "count": len(REGOLITH_DATABASE)
    }


@router.post(
    "/comm-windows",
    response_model=List[CommunicationPass],
    summary="Calculate Daily Communications Windows",
    description="Calculates orbiter relay passes (MRO, Odyssey, TGO) and direct-to-Earth X-band opportunities for given coordinates.",
)
async def get_comm_windows(req: CommWindowsRequest):
    return calculate_comm_windows(lat_deg=req.latitude, lon_deg=req.longitude)


@router.post(
    "/multi-rover-simulation",
    response_model=MultiRoverSimulationResponse,
    summary="Simulate and Compare Multiple Rovers on Identical Traverse",
    description=(
        "Executes a side-by-side simulation of multiple rovers (Perseverance, Curiosity, Opportunity, "
        "Spirit, Zhurong, ExoMars, Hexacopter, Crew Rover) across the identical terrain corridor, "
        "evaluating Bekker terramechanics, slip, energy budgets, mission sols, and multi-criteria risk envelopes."
    ),
    status_code=status.HTTP_200_OK,
)
async def run_multi_rover_simulation(req: MultiRoverSimulationRequest) -> MultiRoverSimulationResponse:
    try:
        # 1. Compute terrain corridor baseline using A* route planner
        route_req = RoutePlanningRequest(
            start=Waypoint(latitude=req.start_latitude, longitude=req.start_longitude),
            destination=Waypoint(latitude=req.destination_latitude, longitude=req.destination_longitude),
            mobility_profile="rover_perseverance",
            preference="minimum_slope"
        )
        route_res = _nav_router.calculate_routes(route_req)
        rec = route_res.recommended_route

        distance_km = rec.total_distance_km
        elev_gain = rec.elevation_gain_m
        max_slope = rec.max_slope_degrees
        mean_slope = rec.mean_slope_degrees
        mean_tri = sum(w.roughness_tri for w in rec.waypoints) / max(1, len(rec.waypoints))

        # 2. Run multi-rover comparison across terrain corridor
        comparison = simulate_multi_rover_comparison(
            distance_km=distance_km,
            elevation_gain_m=elev_gain,
            max_slope_deg=max_slope,
            mean_slope_deg=mean_slope,
            roughness_tri=mean_tri,
            selected_rovers=req.rovers,
            soil_type=req.soil_type,
            ls_deg=req.solar_longitude_ls,
            dust_tau=req.dust_optical_depth_tau,
            lat_deg=req.start_latitude
        )

        regolith = REGOLITH_DATABASE.get(req.soil_type, REGOLITH_DATABASE["basaltic_sand"])

        provenance = ProvenanceFactory.create_rover_simulation_provenance("multi_rover_terramechanics")

        return MultiRoverSimulationResponse(
            status="success",
            corridor_summary={
                "distance_km": distance_km,
                "direct_distance_km": rec.direct_distance_km,
                "elevation_gain_m": elev_gain,
                "elevation_loss_m": rec.elevation_loss_m,
                "max_slope_degrees": max_slope,
                "mean_slope_degrees": mean_slope,
                "mean_roughness_tri": round(mean_tri, 2),
                "hazard_segments_count": rec.hazard_segments_count
            },
            regolith_properties=regolith.model_dump(),
            environmental_conditions={
                "solar_longitude_ls": req.solar_longitude_ls,
                "dust_optical_depth_tau": req.dust_optical_depth_tau,
                "soil_type": req.soil_type
            },
            comparison_results=comparison,
            scientific_provenance=provenance.model_dump()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-rover simulation failed: {str(e)}"
        ) from e
