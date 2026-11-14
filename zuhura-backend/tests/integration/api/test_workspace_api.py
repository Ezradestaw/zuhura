"""
Tests for the workspace API.
Validates:
1. Collaborative study workspaces (listing, creation, status tracking).
2. Structured observation logbook (creation, epistemic classification, PDS links).
3. Scientific hypothesis management (formulation, confidence rating, falsification criteria).
4. Activity feed tracking for collaborative research.
5. Export operations (Publication study manifest GeoJSON package, KML 2.3 rover traverse, LaTeX tables).
"""

import pytest
from httpx import AsyncClient, ASGITransport
from zuhura.api.main import app
from zuhura.workspace.engine import workspace_engine, StudyWorkspace, ScientificObservation, ScientificHypothesis


@pytest.mark.asyncio
async def test_list_studies():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/spatial/workspace/studies")
        assert resp.status_code == 200
        studies = resp.json()
        assert len(studies) >= 3
        ids = [s["study_id"] for s in studies]
        assert "study_jezero_astrobiology" in ids
        assert "study_olympus_lavatubes" in ids
        assert "study_acidalia_water_ice" in ids

        jezero = next(s for s in studies if s["study_id"] == "study_jezero_astrobiology")
        assert jezero["lead_investigator"] != ""
        assert jezero["observations_count"] >= 2
        assert jezero["hypotheses_count"] >= 1


@pytest.mark.asyncio
async def test_create_study():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        new_study = {
            "study_id": "study_gale_strata",
            "name": "Mount Sharp Stratigraphy & Lacustrine Habitability",
            "description": "Analysis of sulfate-bearing units and mudstone transitions in Gale Crater.",
            "lead_investigator": "MSL Science Team",
            "target_region": "Gale Crater / Aeolis Mons",
            "target_latitude": -4.68,
            "target_longitude": 137.38,
            "active_layers": ["viking_mdim21", "ctx_global"],
            "date_created": "2026-11-13",
            "date_modified": "2026-11-13",
            "status": "ACTIVE",
            "observations_count": 0,
            "hypotheses_count": 0
        }
        resp = await client.post("/api/v1/spatial/workspace/studies", json=new_study)
        assert resp.status_code == 200
        created = resp.json()
        assert created["study_id"] == "study_gale_strata"
        assert created["lead_investigator"] == "MSL Science Team"


@pytest.mark.asyncio
async def test_observations_workflow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get existing observations
        resp = await client.get("/api/v1/spatial/workspace/studies/study_jezero_astrobiology/observations")
        assert resp.status_code == 200
        obs_list = resp.json()
        assert len(obs_list) >= 2
        assert any(o["epistemic_classification"] == "MEASURED" for o in obs_list)

        # Add new observation
        new_obs = {
            "latitude": 18.45,
            "longitude": 77.42,
            "elevation_m": -2520.0,
            "observation_type": "ASTROBIOLOGY",
            "title": "Organic Raman Signal in Belva Delta Strata",
            "notes": "SHERLOC arm spectrometer indicates aromatic organic compound fluorescence in fine sandstone.",
            "tags": ["SHERLOC", "Organics", "Belva Crater", "Delta"],
            "epistemic_classification": "MEASURED",
            "attached_data_products": ["urn:nasa:pds:mars2020:sherloc_edr_0029"],
            "uncertainty_m": 0.5
        }
        resp = await client.post(
            "/api/v1/spatial/workspace/studies/study_jezero_astrobiology/observations",
            json=new_obs
        )
        assert resp.status_code == 200
        created_obs = resp.json()
        assert created_obs["observation_type"] == "ASTROBIOLOGY"
        assert created_obs["title"] == "Organic Raman Signal in Belva Delta Strata"
        assert created_obs["epistemic_classification"] == "MEASURED"


@pytest.mark.asyncio
async def test_hypotheses_workflow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get existing hypotheses
        resp = await client.get("/api/v1/spatial/workspace/studies/study_jezero_astrobiology/hypotheses")
        assert resp.status_code == 200
        hyps = resp.json()
        assert len(hyps) >= 2
        assert any(h["status"] == "SUPPORTED" for h in hyps)

        # Formulate new hypothesis
        new_hyp = {
            "statement": "Episodic hyper-saline brines formed sulfate crusts during late-stage lake evaporation.",
            "status": "HYPOTHESIZED",
            "confidence_rating": 0.68,
            "linked_evidence_ids": ["obs_001"],
            "competing_hypotheses": ["Percolation of hydrothermal subsurface volcanic fluids."],
            "falsification_criteria": "Absence of halite or gypsum crystals in delta scarp mineral matrix."
        }
        resp = await client.post(
            "/api/v1/spatial/workspace/studies/study_jezero_astrobiology/hypotheses",
            json=new_hyp
        )
        assert resp.status_code == 200
        created_hyp = resp.json()
        assert created_hyp["status"] == "HYPOTHESIZED"
        assert created_hyp["confidence_rating"] == 0.68


@pytest.mark.asyncio
async def test_activity_feed():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/spatial/workspace/studies/study_jezero_astrobiology/activity")
        assert resp.status_code == 200
        activities = resp.json()
        assert len(activities) >= 2
        types = [a["action_type"] for a in activities]
        assert "HYPOTHESIS_UPDATE" in types or "OBSERVATION_ADDED" in types


@pytest.mark.asyncio
async def test_exports_manifest_kml_latex():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Export study package manifest
        resp = await client.post("/api/v1/spatial/workspace/studies/study_jezero_astrobiology/export/manifest")
        assert resp.status_code == 200
        manifest = resp.json()
        assert "study_manifest" in manifest
        assert manifest["study_manifest"]["study_id"] == "study_jezero_astrobiology"
        assert "geojson" in manifest
        assert manifest["geojson"]["type"] == "FeatureCollection"
        assert len(manifest["geojson"]["features"]) >= 2
        assert "scientific_provenance" in manifest
        assert "citation" in manifest

        # 2. Export KML traverse
        kml_payload = {
            "route_name": "Perseverance Sol 210-215 Traverse",
            "waypoints": [
                {"latitude": 18.38, "longitude": 77.58, "elevation_m": -2500.0},
                {"latitude": 18.40, "longitude": 77.55, "elevation_m": -2515.0},
                {"latitude": 18.42, "longitude": 77.48, "elevation_m": -2530.0}
            ]
        }
        resp = await client.post("/api/v1/spatial/workspace/export/kml", json=kml_payload)
        assert resp.status_code == 200
        assert "application/vnd.google-earth.kml+xml" in resp.headers["content-type"]
        kml_content = resp.text
        assert "<?xml version=" in kml_content
        assert "<kml xmlns=" in kml_content
        assert "Perseverance Sol 210-215 Traverse" in kml_content
        assert "<coordinates>" in kml_content

        # 3. Export LaTeX table
        resp = await client.get("/api/v1/spatial/workspace/export/latex?table_type=crater_morphometry")
        assert resp.status_code == 200
        latex_data = resp.json()
        assert latex_data["table_type"] == "crater_morphometry"
        assert r"\begin{table}" in latex_data["latex"]
        assert r"Jezero Basin" in latex_data["latex"]
        assert r"\end{table}" in latex_data["latex"]

        resp2 = await client.get("/api/v1/spatial/workspace/export/latex?table_type=terramechanics")
        assert resp2.status_code == 200
        latex_data2 = resp2.json()
        assert r"Perseverance" in latex_data2["latex"]
        assert r"Bekker Sinkage" in latex_data2["latex"]
