"""
Planetary interior model endpoints.
Serves interior cross-section layers, thermodynamic boundaries,
and InSight seismic provenance.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from zuhura.interior.model import (
    MarsInteriorModel,
    InteriorLayer,
    MARS_INTERIOR_LAYERS,
    get_mars_interior_summary,
    compare_interior_models,
)

router = APIRouter()


class CrossSectionSliceResponse(BaseModel):
    planetary_radius_km: float
    layers: List[InteriorLayer]
    selected_layer: Optional[InteriorLayer] = None
    cutaway_angle_degrees: float
    data_vintage: str
    provenance_doi: str = "10.1126/science.abf8966"
    disclaimer: str = (
        "Mars planetary interior structure is derived from NASA InSight SEIS mission seismic inversions, "
        "MRO gravity fields, and mineral physics models. Boundaries are subject to observational uncertainties."
    )


@router.get(
    "/layers",
    response_model=List[InteriorLayer],
    summary="List Planetary Interior Layers & Physical Properties",
    description="Returns all scientifically validated structural layers of Mars from crust to liquid metallic core.",
)
async def list_interior_layers() -> List[InteriorLayer]:
    return MARS_INTERIOR_LAYERS


@router.get(
    "/model",
    response_model=MarsInteriorModel,
    summary="Mars Planetary Interior Geophysical Model",
    description="Returns the full geomechanical, thermal, and compositional interior model of Mars.",
)
async def get_interior_model(
    profile: str = Query(
        default="samuel_2023_basal_molten",
        description="Model profile: 'samuel_2023_basal_molten' (consensus) or 'stahler_2021_large_core' (historical)"
    )
) -> MarsInteriorModel:
    return get_mars_interior_summary(profile=profile)


@router.get(
    "/compare",
    summary="Compare InSight Planetary Interior Publications",
    description="Provides comparative analysis between Stähler et al. (2021) and Samuel/Khan et al. (2023) Nature consensus.",
)
async def get_interior_model_comparison() -> Dict[str, Any]:
    return compare_interior_models()


@router.get(
    "/cross-section",
    response_model=CrossSectionSliceResponse,
    summary="Generate 3D Cutaway Cross-Section Parameters",
    description="Provides geometry, radial depths, and physical parameters for interactive 3D planetary cross-sections.",
)
async def get_cross_section(
    cutaway_angle: float = Query(default=90.0, ge=10.0, le=180.0, description="Cutaway wedge angle in degrees"),
    layer_id: Optional[str] = Query(default=None, description="Optional layer ID to highlight"),
) -> CrossSectionSliceResponse:
    selected = None
    if layer_id:
        for layer in MARS_INTERIOR_LAYERS:
            if layer.id == layer_id:
                selected = layer
                break
        if not selected:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Interior layer '{layer_id}' not found.",
            )

    return CrossSectionSliceResponse(
        planetary_radius_km=3389.5,
        layers=MARS_INTERIOR_LAYERS,
        selected_layer=selected,
        cutaway_angle_degrees=cutaway_angle,
        data_vintage="NASA InSight Final Archive / Science (2021-2023)",
    )
