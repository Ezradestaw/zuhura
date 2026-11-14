"""
Data provenance and epistemic status endpoints.
Provides standardized epistemic classifications, uncertainty models, dataset provenance,
and multi-model scientific reconciliation across planetary datasets.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from zuhura.provenance.taxonomy import (
    EpistemicClassification,
    UncertaintyModel,
    ScientificReference,
    ScientificProvenanceRecord,
    ProvenanceFactory,
)
from zuhura.provenance.reproducibility import (
    ComputationManifest,
    create_computation_manifest,
    generate_computation_hash,
)

router = APIRouter()


class CompetingModelComparison(BaseModel):
    subject: str
    competing_interpretations: List[Dict[str, Any]]
    scientific_consensus: str
    reconciliation_details: str
    provenance_records: List[ScientificProvenanceRecord]


class ManifestVerificationRequest(BaseModel):
    algorithm_name: str
    algorithm_version: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    duration_ms: float = 0.0


@router.get("/classifications", summary="List Epistemic Classifications", tags=["Scientific Truth Engine"])
async def get_epistemic_classifications():
    """Returns the standardized epistemic classifications and definitions."""
    return {
        "classifications": [
            {
                "id": EpistemicClassification.OBSERVED.value,
                "label": "Observed",
                "color": "#10b981",
                "description": "Directly observed by calibrated remote sensing instruments (e.g., optical reflectance, calibrated spectral radiance)."
            },
            {
                "id": EpistemicClassification.MEASURED.value,
                "label": "Measured",
                "color": "#06b6d4",
                "description": "Physical sensor measurements (e.g., MOLA laser altimetry pulse transit times, InSight seismometer velocity records)."
            },
            {
                "id": EpistemicClassification.DERIVED.value,
                "label": "Derived",
                "color": "#3b82f6",
                "description": "Computed via deterministic mathematical transformations or physical equations (e.g., Horn slope gradient, TRI roughness, geodesic distances)."
            },
            {
                "id": EpistemicClassification.MODEL_ESTIMATED.value,
                "label": "Model Estimated",
                "color": "#f59e0b",
                "description": "Geophysical, mineralogical, or interior structure inversions based on physical models (e.g., core radius, mantle velocity profiles)."
            },
            {
                "id": EpistemicClassification.SIMULATED.value,
                "label": "Simulated",
                "color": "#8b5cf6",
                "description": "Scenario pathfinding and physical vehicle terramechanics simulations (e.g., Bekker wheel slip, rover energy expenditure)."
            },
            {
                "id": EpistemicClassification.PROVISIONAL.value,
                "label": "Provisional",
                "color": "#e07a5f",
                "description": "Automated algorithmic classifications not yet formally approved by the IAU Working Group for Planetary System Nomenclature."
            },
            {
                "id": EpistemicClassification.UNVERIFIED.value,
                "label": "Unverified",
                "color": "#ef4444",
                "description": "Working scientific hypotheses or provisional estimates requiring additional empirical confirmation."
            }
        ]
    }


@router.get("/datasets", summary="List Scientific Datasets Provenance", tags=["Scientific Truth Engine"])
async def get_all_dataset_provenance():
    """Returns standardized provenance records for all primary planetary datasets."""
    records = [
        ProvenanceFactory.create_mola_elevation_provenance(),
        ProvenanceFactory.create_viking_basemap_provenance(),
        ProvenanceFactory.create_ctx_mosaic_provenance(),
        ProvenanceFactory.create_hirise_provenance(),
        ProvenanceFactory.create_insight_interior_provenance("samuel_2023_basal_molten"),
        ProvenanceFactory.create_insight_interior_provenance("stahler_2021_large_core"),
        ProvenanceFactory.create_morphometry_provenance("slope"),
        ProvenanceFactory.create_rover_simulation_provenance("rover_perseverance"),
        ProvenanceFactory.create_provisional_region_provenance(),
    ]
    return {
        "status": "success",
        "total_records": len(records),
        "geodetic_datum": "IAU/IAG 2015 WGCCRE",
        "vertical_datum": "Mars Areoid (MOLA GMM-3 / MEG128)",
        "records": [r.model_dump() for r in records]
    }


@router.get("/datasets/{dataset_id}", summary="Get Specific Dataset Provenance", tags=["Scientific Truth Engine"])
async def get_dataset_provenance_by_id(dataset_id: str):
    """Fetches full provenance record for a specific scientific dataset or model."""
    id_upper = dataset_id.upper()
    if "MOLA" in id_upper:
        record = ProvenanceFactory.create_mola_elevation_provenance()
    elif "VIKING" in id_upper:
        record = ProvenanceFactory.create_viking_basemap_provenance()
    elif "CTX" in id_upper:
        record = ProvenanceFactory.create_ctx_mosaic_provenance()
    elif "HIRISE" in id_upper:
        record = ProvenanceFactory.create_hirise_provenance()
    elif "INSIGHT" in id_upper or "INTERIOR" in id_upper:
        record = ProvenanceFactory.create_insight_interior_provenance("samuel_2023_basal_molten")
    elif "ROVER" in id_upper or "MOBILITY" in id_upper:
        record = ProvenanceFactory.create_rover_simulation_provenance("rover_perseverance")
    elif "REGION" in id_upper or "DISCOVERY" in id_upper:
        record = ProvenanceFactory.create_provisional_region_provenance()
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provenance record for dataset '{dataset_id}' not found. Supported keys: MOLA, VIKING, CTX, HIRISE, INSIGHT, ROVER, REGION."
        )
    return record.model_dump()


@router.get("/competing-models", summary="Compare Competing Scientific Models", tags=["Scientific Truth Engine"])
async def get_competing_models():
    """Returns side-by-side reconciliation of competing planetary scientific models."""
    insight_comp = CompetingModelComparison(
        subject="Mars Core Radius & Basal Magma Ocean (InSight SEIS)",
        competing_interpretations=[
            {
                "model_id": "stahler_2021",
                "model_name": "InSight Initial Large-Core Model (Stähler et al., Science 2021)",
                "apparent_core_radius_km": 1830.0,
                "uncertainty_km": "± 40 km",
                "core_density_kg_m3": "5,700 – 6,300",
                "light_elements_wt_pct": "20 – 22 wt% (implausibly volatile-rich)",
                "has_basal_molten_layer": False,
                "status": "SUPERSEDED",
                "notes": "Interpreted core-reflected shear wave (ScS) travel times assuming a solid silicate mantle extending directly to the core-mantle boundary."
            },
            {
                "model_id": "samuel_khan_2023",
                "model_name": "Nature 2023 Reconciled Model (Samuel et al. & Khan et al., Nature 2023)",
                "apparent_core_radius_km": 1650.0,
                "uncertainty_km": "± 20 km",
                "core_density_kg_m3": "6,100 – 6,300",
                "light_elements_wt_pct": "15 – 18 wt% (chemically consistent with cosmochemical models)",
                "has_basal_molten_layer": True,
                "basal_layer_thickness_km": "150 – 170 km",
                "status": "CURRENT_CONSENSUS",
                "notes": "Demonstrated that earlier reflected seismic waves reflected not from the metallic core, but from the top of a ~160 km thick basal molten silicate slag layer blanket decoupling the core."
            }
        ],
        scientific_consensus="Reconciled core radius R = 1,650 ± 20 km surrounded by a 150-170 km basal molten silicate slag layer atop the liquid metallic core.",
        reconciliation_details="Zuhura supports both models in the geophysics engine. The Nature 2023 model is the active scientific default, with full provenance tracking of the 2021 historical inversion.",
        provenance_records=[
            ProvenanceFactory.create_insight_interior_provenance("samuel_2023_basal_molten"),
            ProvenanceFactory.create_insight_interior_provenance("stahler_2021_large_core"),
        ]
    )

    crust_comp = CompetingModelComparison(
        subject="Martian Crustal Layering & Thickness (Knapmeyer-Endrun et al., Science 2021)",
        competing_interpretations=[
            {
                "model_id": "2_layer_crust",
                "model_name": "Two-Layer Crustal Model",
                "average_thickness_km": "39 ± 8 km",
                "crustal_density_kg_m3": "2,580 – 2,800",
                "status": "PLAUSIBLE_ALTERNATIVE",
                "notes": "Upper porous fractured layer (8-11 km) underlain by uniform middle/lower basaltic crust."
            },
            {
                "model_id": "3_layer_crust",
                "model_name": "Three-Layer Crustal Model (Preferred)",
                "average_thickness_km": "45 ± 10 km",
                "crustal_density_kg_m3": "2,550 – 3,100",
                "status": "PREFERRED_CONSENSUS",
                "notes": "Upper fractured regolith (10 km), middle altered basaltic layer (20 km), and lower dense mafic/granulitic crust (15 km)."
            }
        ],
        scientific_consensus="Receiver function modeling favors a 3-layer crust of ~45 km thickness at InSight station XB.ELYSE.",
        reconciliation_details="Both layering interpretations are represented in the Zuhura InSight X-Ray geophysics suite.",
        provenance_records=[
            ProvenanceFactory.create_insight_interior_provenance("samuel_2023_basal_molten")
        ]
    )

    return {
        "status": "success",
        "comparisons": [
            insight_comp.model_dump(),
            crust_comp.model_dump()
        ]
    }


@router.post("/manifest", summary="Generate & Verify Computation Manifest", tags=["Scientific Truth Engine"])
async def create_manifest(req: ManifestVerificationRequest):
    """Creates a cryptographically hashed, reproducible computation manifest."""
    provenance = ProvenanceFactory.create_morphometry_provenance(req.algorithm_name)
    manifest = create_computation_manifest(
        algorithm_name=req.algorithm_name,
        algorithm_version=req.algorithm_version,
        inputs=req.inputs,
        outputs=req.outputs,
        duration_ms=req.duration_ms,
        provenance=provenance
    )
    return manifest.model_dump()