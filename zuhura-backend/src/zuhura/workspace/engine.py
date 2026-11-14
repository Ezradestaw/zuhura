"""
Workspace storage: studies, observations, hypotheses and activity.
Implements:
1. Multi-study project workspaces (Jezero, Olympus Mons, Acidalia).
2. Structured observation logbook with PDS attachment references and epistemic classifications.
3. Multi-status hypothesis tracker with linked evidence and falsification criteria.
4. Measurement history with geodetic interpretations.
5. Multi-user collaboration activity feeds.
6. Publication export generators (Study Package Manifest, KML, LaTeX tables).

References:
- NASA Planetary Data System (PDS) Standards Reference v1.21.
- Open Geospatial Consortium (OGC) KML 2.3 standard.
- Grotzinger, J. P., et al. (2014). A habitable fluvio-lacustrine environment at Yellowknife Bay, Gale Crater. Science.
"""

import math
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

from zuhura.provenance.taxonomy import ProvenanceFactory, EpistemicClassification


class StudyWorkspace(BaseModel):
    study_id: str
    name: str
    description: str
    lead_investigator: str
    target_region: str
    target_latitude: float
    target_longitude: float
    active_layers: List[str]
    date_created: str
    date_modified: str
    status: str  # "ACTIVE", "ARCHIVED", "PUBLISHED"
    observations_count: int = 0
    hypotheses_count: int = 0


class ScientificObservation(BaseModel):
    obs_id: str
    study_id: str
    timestamp: str
    latitude: float
    longitude: float
    elevation_m: float
    observation_type: str  # "GEOMORPHOLOGY", "MINERALOGY", "ATMOSPHERIC", "MOBILITY_HAZARD", "ASTROBIOLOGY"
    title: str
    notes: str
    tags: List[str]
    epistemic_classification: str = "OBSERVED"
    attached_data_products: List[str]
    uncertainty_m: float = 1.0


class ScientificHypothesis(BaseModel):
    hypothesis_id: str
    study_id: str
    statement: str
    status: str  # "HYPOTHESIZED", "SUPPORTED", "CONTRADICTED", "REFINED", "ABANDONED"
    confidence_rating: float = Field(ge=0.0, le=1.0)
    linked_evidence_ids: List[str]
    competing_hypotheses: List[str]
    falsification_criteria: str
    date_formulated: str
    date_updated: str


class MeasurementRecord(BaseModel):
    record_id: str
    study_id: str
    mode: str  # "distance", "area", "transect_profile"
    points: List[Dict[str, float]]
    result_value: float
    unit: str
    scientific_interpretation: str
    timestamp: str


class ActivityFeedItem(BaseModel):
    activity_id: str
    study_id: str
    author: str
    action_type: str  # "COMMENT", "HYPOTHESIS_UPDATE", "OBSERVATION_ADDED", "ROUTE_SHARED"
    content: str
    timestamp: str


# Example studies shown in a new workspace. Names and roles are placeholders.
DEFAULT_STUDIES: List[StudyWorkspace] = [
    StudyWorkspace(
        study_id="study_jezero_astrobiology",
        name="Jezero Delta Astrobiology & Biosignature Survey",
        description="Investigation of lacustrine delta bottomset beds, smectite clay preservation, and rover sampling corridors.",
        lead_investigator="Example study (sample data)",
        target_region="Jezero Crater, Nili Fossae",
        target_latitude=18.38,
        target_longitude=77.58,
        active_layers=["viking_mdim21", "ctx_global", "hirise_overlays", "mola_areoid"],
        date_created="2026-10-15",
        date_modified="2026-11-13",
        status="ACTIVE",
        observations_count=4,
        hypotheses_count=2
    ),
    StudyWorkspace(
        study_id="study_olympus_lavatubes",
        name="Olympus Mons Lava Tube Reconnaissance",
        description="Subsurface cavernous conduit detection and collapse pit mapping for future pressurized crew habitats.",
        lead_investigator="Example study (sample data)",
        target_region="Olympus Mons Volcanic Caldera",
        target_latitude=18.65,
        target_longitude=226.20,
        active_layers=["viking_mdim21", "mola_color_elevation", "themis_ir_day"],
        date_created="2026-10-20",
        date_modified="2026-11-10",
        status="ACTIVE",
        observations_count=2,
        hypotheses_count=1
    ),
    StudyWorkspace(
        study_id="study_acidalia_water_ice",
        name="Acidalia Planitia Water-Ice In-Situ Feasibility",
        description="Assessment of shallow subsurface excess ice deposits and boulder distributions for human ISRU propellant production.",
        lead_investigator="Example study (sample data)",
        target_region="Acidalia Planitia Northern Lowlands",
        target_latitude=46.70,
        target_longitude=330.10,
        active_layers=["viking_mdim21", "ctx_global", "mola_slope"],
        date_created="2026-11-01",
        date_modified="2026-11-12",
        status="ACTIVE",
        observations_count=3,
        hypotheses_count=1
    )
]

DEFAULT_OBSERVATIONS: List[ScientificObservation] = [
    ScientificObservation(
        obs_id="obs_001",
        study_id="study_jezero_astrobiology",
        timestamp="2026-11-12 14:22 UTC",
        latitude=18.42,
        longitude=77.48,
        elevation_m=-2530.0,
        observation_type="MINERALOGY",
        title="Fe/Mg Smectite Clay Absorption at Kodiak Scarp",
        notes="CRISM spectral extraction shows strong 2.30 µm absorption characteristic of iron-magnesium smectite clays.",
        tags=["CRISM", "Smectite", "Clay", "Delta"],
        epistemic_classification="MEASURED",
        attached_data_products=["urn:nasa:pds:crism_mtrdr:frt00003e12_07_if165l_trr3"],
        uncertainty_m=0.8
    ),
    ScientificObservation(
        obs_id="obs_002",
        study_id="study_jezero_astrobiology",
        timestamp="2026-11-13 09:45 UTC",
        latitude=18.36,
        longitude=77.54,
        elevation_m=-2570.0,
        observation_type="MOBILITY_HAZARD",
        title="Active Aeolian Basaltic TAR Megaripples in Séítah",
        notes="High wheel slip (> 35%) and 8 cm sinkage risk identified along ripple crests; recommended traverse diversion.",
        tags=["Hazcam", "Slip", "Dune", "Séítah"],
        epistemic_classification="DERIVED",
        attached_data_products=["urn:nasa:pds:mars2020:navcam_ortho_sol215"],
        uncertainty_m=1.2
    )
]

DEFAULT_HYPOTHESES: List[ScientificHypothesis] = [
    ScientificHypothesis(
        hypothesis_id="hyp_001",
        study_id="study_jezero_astrobiology",
        statement="Kodiak Butte represents an erosional deltaic remnant deposited into a sustained standing body of water (depth > 30m).",
        status="SUPPORTED",
        confidence_rating=0.92,
        linked_evidence_ids=["obs_001", "crater_jezero_profile"],
        competing_hypotheses=["Subaerial catastrophic flash-flood debris fan"],
        falsification_criteria="Absence of fine-grained bottomset laminae or discovery of unstratified volcanic breccia at scarp base.",
        date_formulated="2026-10-18",
        date_updated="2026-11-13"
    ),
    ScientificHypothesis(
        hypothesis_id="hyp_002",
        study_id="study_jezero_astrobiology",
        statement="Subsurface organic carbon biosignatures are concentrated in fine-grained mudstones at the delta front.",
        status="HYPOTHESIZED",
        confidence_rating=0.74,
        linked_evidence_ids=["obs_001"],
        competing_hypotheses=["Complete oxidation by atmospheric perchlorates and UV photolysis."],
        falsification_criteria="Zero organic Raman or fluorescent signal detected by SHERLOC in deep core samples.",
        date_formulated="2026-10-25",
        date_updated="2026-11-11"
    )
]

DEFAULT_ACTIVITIES: List[ActivityFeedItem] = [
    ActivityFeedItem(
        activity_id="act_001",
        study_id="study_jezero_astrobiology",
        author="Study Lead",
        action_type="HYPOTHESIS_UPDATE",
        content="Updated Hypothesis HYP-001 to SUPPORTED status following Kodiak scarp strata confirmation.",
        timestamp="2026-11-13 10:15 UTC"
    ),
    ActivityFeedItem(
        activity_id="act_002",
        study_id="study_jezero_astrobiology",
        author="Rover Mobility Lead",
        action_type="ROUTE_SHARED",
        content="Generated optimized minimum-slope AutoNav corridor avoiding Séítah TAR dune fields.",
        timestamp="2026-11-13 11:30 UTC"
    )
]


class WorkspaceEngine:
    """Manages collaborative studies, observations, hypotheses, and publication exports."""

    def __init__(self):
        self.studies: Dict[str, StudyWorkspace] = {s.study_id: s for s in DEFAULT_STUDIES}
        self.observations: Dict[str, ScientificObservation] = {o.obs_id: o for o in DEFAULT_OBSERVATIONS}
        self.hypotheses: Dict[str, ScientificHypothesis] = {h.hypothesis_id: h for h in DEFAULT_HYPOTHESES}
        self.activities: List[ActivityFeedItem] = list(DEFAULT_ACTIVITIES)

    def list_studies(self) -> List[StudyWorkspace]:
        # Update counts
        for s in self.studies.values():
            s.observations_count = sum(1 for o in self.observations.values() if o.study_id == s.study_id)
            s.hypotheses_count = sum(1 for h in self.hypotheses.values() if h.study_id == s.study_id)
        return list(self.studies.values())

    def create_study(self, study: StudyWorkspace) -> StudyWorkspace:
        self.studies[study.study_id] = study
        return study

    def get_study_observations(self, study_id: str) -> List[ScientificObservation]:
        return [o for o in self.observations.values() if o.study_id == study_id]

    def add_observation(self, obs: ScientificObservation) -> ScientificObservation:
        self.observations[obs.obs_id] = obs
        self.activities.append(ActivityFeedItem(
            activity_id=f"act_{int(time.time()*1000)}",
            study_id=obs.study_id,
            author="Contributing Researcher",
            action_type="OBSERVATION_ADDED",
            content=f"Logged new {obs.observation_type} observation: '{obs.title}'",
            timestamp=obs.timestamp
        ))
        return obs

    def get_study_hypotheses(self, study_id: str) -> List[ScientificHypothesis]:
        return [h for h in self.hypotheses.values() if h.study_id == study_id]

    def add_hypothesis(self, hyp: ScientificHypothesis) -> ScientificHypothesis:
        self.hypotheses[hyp.hypothesis_id] = hyp
        self.activities.append(ActivityFeedItem(
            activity_id=f"act_{int(time.time()*1000)}",
            study_id=hyp.study_id,
            author="Contributing Researcher",
            action_type="HYPOTHESIS_UPDATE",
            content=f"Formulated hypothesis: '{hyp.statement[:60]}...'",
            timestamp=hyp.date_updated
        ))
        return hyp

    def get_activity_feed(self, study_id: str) -> List[ActivityFeedItem]:
        return [a for a in self.activities if a.study_id == study_id]

    def export_study_package(self, study_id: str) -> Dict[str, Any]:
        """Generates comprehensive publication-ready scientific study manifest."""
        study = self.studies.get(study_id)
        if not study:
            raise ValueError(f"Study '{study_id}' not found.")

        obs_list = self.get_study_observations(study_id)
        hyp_list = self.get_study_hypotheses(study_id)

        # Generate GeoJSON feature collection of observations
        features = []
        for o in obs_list:
            features.append({
                "type": "Feature",
                "properties": {
                    "obs_id": o.obs_id,
                    "title": o.title,
                    "type": o.observation_type,
                    "elevation_m": o.elevation_m,
                    "notes": o.notes,
                    "epistemic_classification": o.epistemic_classification,
                    "tags": o.tags
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [o.longitude, o.latitude, o.elevation_m]
                }
            })

        provenance = ProvenanceFactory.create_morphometry_provenance(derivative_type="collaborative_study_dossier")

        return {
            "study_manifest": {
                "study_id": study.study_id,
                "title": study.name,
                "description": study.description,
                "lead_investigator": study.lead_investigator,
                "target_region": study.target_region,
                "target_coordinates": {"lat": study.target_latitude, "lon": study.target_longitude},
                "status": study.status,
                "export_date_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "total_observations": len(obs_list),
                "total_hypotheses": len(hyp_list),
            },
            "observations": [o.model_dump() for o in obs_list],
            "hypotheses": [h.model_dump() for h in hyp_list],
            "geojson": {
                "type": "FeatureCollection",
                "features": features
            },
            "scientific_provenance": provenance.model_dump(),
            "citation": f"{study.lead_investigator} (2026). {study.name}. Zuhura Mars Digital Twin Study Archive, URN:nasa:pds:zuhura:study:{study.study_id}"
        }

    def export_kml_traverse(
        self,
        route_name: str,
        waypoints: List[Dict[str, float]]
    ) -> str:
        """Generates standard OGC KML 2.3 rover traverse file for planetary GIS."""
        coords_str = " ".join(f"{w.get('longitude', 0)},{w.get('latitude', 0)},{w.get('elevation_m', 0)}" for w in waypoints)

        kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{route_name}</name>
    <description>Zuhura Planetary Digital Twin - Mars Rover Traverse Corridor</description>
    <Style id="roverTraverseLine">
      <LineStyle>
        <color>ff10b981</color>
        <width>4</width>
      </LineStyle>
    </Style>
    <Placemark>
      <name>{route_name}</name>
      <styleUrl>#roverTraverseLine</styleUrl>
      <LineString>
        <extrude>1</extrude>
        <tessellate>1</tessellate>
        <altitudeMode>clampToGround</altitudeMode>
        <coordinates>
          {coords_str}
        </coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>"""
        return kml.strip()

    def generate_latex_table(self, table_type: str = "crater_morphometry") -> str:
        """Generates publication-ready LaTeX table snippets for manuscripts."""
        if table_type == "crater_morphometry":
            return r"""\begin{table}[htbp]
\centering
\caption{Morphometric Parameters of Target Martian Impact Craters (Pike 1980 / Barlow 2000)}
\label{tab:crater_morphometry}
\begin{tabular}{lcccccc}
\hline
\textbf{Crater Basin} & \textbf{Lat (°N)} & \textbf{Lon (°E)} & \textbf{Diameter (km)} & \textbf{Depth (m)} & \textbf{$d/D$} & \textbf{Class} \\
\hline
Jezero Basin & 18.38 & 77.58 & 47.5 & 1050 & 0.0221 & Complex \\
Kodiak Remnant & 18.42 & 77.48 & 3.2 & 640 & 0.2000 & Simple \\
Gale Basin & -4.68 & 137.38 & 154.0 & 4120 & 0.0267 & Complex \\
Newton Crater & -40.50 & 158.10 & 298.0 & 5800 & 0.0195 & Multi-Ring \\
\hline
\end{tabular}
\end{table}"""
        elif table_type == "terramechanics":
            return r"""\begin{table}[htbp]
\centering
\caption{Terramechanical Mobility and Energy Budget Comparison across Regolith Facies}
\label{tab:terramechanics_comparison}
\begin{tabular}{lccccc}
\hline
\textbf{Rover Profile} & \textbf{Mass (kg)} & \textbf{Power (W)} & \textbf{Max Slip (\%)} & \textbf{Bekker Sinkage (cm)} & \textbf{Risk Rating} \\
\hline
Perseverance & 1025 & 110 (MMRTG) & 12.4 & 2.4 & BENIGN \\
Curiosity & 899 & 110 (MMRTG) & 11.8 & 2.2 & BENIGN \\
Opportunity & 185 & 140 (Solar PV) & 18.6 & 4.8 & ELEVATED \\
Spirit (Degraded) & 185 & 140 (Solar PV) & 32.4 & 5.2 & HAZARDOUS \\
Aerial Scout & 2.4 & 350 (Battery) & 0.0 & 0.0 & BENIGN \\
\hline
\end{tabular}
\end{table}"""
        return "% Unsupported table type"


workspace_engine = WorkspaceEngine()
