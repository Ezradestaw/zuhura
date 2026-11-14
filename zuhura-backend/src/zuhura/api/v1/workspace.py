"""
Workspace endpoints: studies, notes, bookmarks and exports.
Provides endpoints for collaborative studies, observation logbook, hypothesis tracking,
activity feeds, and publication-ready exports (manifests, KML, LaTeX tables).
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from zuhura.workspace.engine import (
    workspace_engine,
    StudyWorkspace,
    ScientificObservation,
    ScientificHypothesis,
    ActivityFeedItem
)

router = APIRouter()


class KmlExportRequest(BaseModel):
    route_name: str = "Jezero Delta Traverse"
    waypoints: List[Dict[str, float]] = Field(
        default_factory=lambda: [
            {"latitude": 18.38, "longitude": 77.58, "elevation_m": -2500.0},
            {"latitude": 18.42, "longitude": 77.48, "elevation_m": -2530.0}
        ]
    )


class ObservationCreateRequest(BaseModel):
    latitude: float
    longitude: float
    elevation_m: float
    observation_type: str = "GEOMORPHOLOGY"
    title: str
    notes: str
    tags: List[str] = Field(default_factory=list)
    epistemic_classification: str = "OBSERVED"
    attached_data_products: List[str] = Field(default_factory=list)
    uncertainty_m: float = 1.0


class HypothesisCreateRequest(BaseModel):
    statement: str
    status: str = "HYPOTHESIZED"
    confidence_rating: float = Field(default=0.7, ge=0.0, le=1.0)
    linked_evidence_ids: List[str] = Field(default_factory=list)
    competing_hypotheses: List[str] = Field(default_factory=list)
    falsification_criteria: str = ""


@router.get("/studies", response_model=List[StudyWorkspace], summary="List Collaborative Studies")
async def list_studies():
    """Returns all active, archived, or published planetary science study workspaces."""
    return workspace_engine.list_studies()


@router.post("/studies", response_model=StudyWorkspace, summary="Create Study Workspace")
async def create_study(study: StudyWorkspace):
    """Registers a new collaborative study workspace for Mars exploration."""
    return workspace_engine.create_study(study)


@router.get("/studies/{study_id}/observations", response_model=List[ScientificObservation], summary="Get Study Observations")
async def get_study_observations(study_id: str):
    """Retrieves all logged scientific observations for the specified study."""
    return workspace_engine.get_study_observations(study_id)


@router.post("/studies/{study_id}/observations", response_model=ScientificObservation, summary="Log Scientific Observation")
async def add_observation(study_id: str, req: ObservationCreateRequest):
    """Logs a new structured scientific observation with epistemic classification and PDS product links."""
    import time
    obs = ScientificObservation(
        obs_id=f"obs_{int(time.time() * 1000)}",
        study_id=study_id,
        timestamp=time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
        latitude=req.latitude,
        longitude=req.longitude,
        elevation_m=req.elevation_m,
        observation_type=req.observation_type,
        title=req.title,
        notes=req.notes,
        tags=req.tags,
        epistemic_classification=req.epistemic_classification,
        attached_data_products=req.attached_data_products,
        uncertainty_m=req.uncertainty_m
    )
    return workspace_engine.add_observation(obs)


@router.get("/studies/{study_id}/hypotheses", response_model=List[ScientificHypothesis], summary="Get Study Hypotheses")
async def get_study_hypotheses(study_id: str):
    """Retrieves all working scientific hypotheses for the specified study."""
    return workspace_engine.get_study_hypotheses(study_id)


@router.post("/studies/{study_id}/hypotheses", response_model=ScientificHypothesis, summary="Formulate or Update Hypothesis")
async def add_hypothesis(study_id: str, req: HypothesisCreateRequest):
    """Formulates a new working hypothesis with falsification criteria and epistemic confidence."""
    import time
    now_str = time.strftime("%Y-%m-%d", time.gmtime())
    hyp = ScientificHypothesis(
        hypothesis_id=f"hyp_{int(time.time() * 1000)}",
        study_id=study_id,
        statement=req.statement,
        status=req.status,
        confidence_rating=req.confidence_rating,
        linked_evidence_ids=req.linked_evidence_ids,
        competing_hypotheses=req.competing_hypotheses,
        falsification_criteria=req.falsification_criteria,
        date_formulated=now_str,
        date_updated=now_str
    )
    return workspace_engine.add_hypothesis(hyp)


@router.get("/studies/{study_id}/activity", response_model=List[ActivityFeedItem], summary="Get Study Activity Feed")
async def get_study_activity(study_id: str):
    """Returns collaboration events, hypothesis status transitions, and logbook entries."""
    return workspace_engine.get_activity_feed(study_id)


@router.post("/studies/{study_id}/export/manifest", summary="Export Study Package Manifest")
async def export_study_package(study_id: str):
    """Generates complete publication-grade study manifest with GeoJSON and scientific provenance."""
    try:
        return workspace_engine.export_study_package(study_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/export/kml", summary="Export Traverse as OGC KML")
async def export_kml(req: KmlExportRequest):
    """Exports rover traverse corridors as standard OGC KML 2.3 XML."""
    kml_str = workspace_engine.export_kml_traverse(req.route_name, req.waypoints)
    return Response(content=kml_str, media_type="application/vnd.google-earth.kml+xml")


@router.get("/export/latex", summary="Generate Publication LaTeX Table")
async def export_latex(table_type: str = Query("crater_morphometry", description="Table type: 'crater_morphometry' or 'terramechanics'")):
    """Generates camera-ready LaTeX table snippets conforming to AGU/Planetary Science Journal standards."""
    latex_code = workspace_engine.generate_latex_table(table_type)
    return {"table_type": table_type, "latex": latex_code}
