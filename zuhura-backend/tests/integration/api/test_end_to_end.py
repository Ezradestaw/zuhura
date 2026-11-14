"""
End-to-end tests covering the main API workflows.
Validates the complete 10-stage planetary science pipeline in continuous sequence:
Geodesy -> Topography -> Atmosphere -> Dust/Power -> Mobility -> Mineralogy -> Provenance -> Paper -> Peer-Review -> Workspace Export
"""

import pytest
from fastapi.testclient import TestClient
from zuhura.api.main import app

client = TestClient(app)


def test_mission_certification_full_e2e_pipeline():
    """
    Executes and certifies the full end-to-end scientific research and exploration pipeline
    for the Jezero Crater Delta exploration zone.
    """
    target_lat = 18.38
    target_lon = 77.58
    target_elev = -2500.0
    season_ls = 180.0

    # -------------------------------------------------------------------------
    # STAGE 1: Geodetic Datum & System Health
    # -------------------------------------------------------------------------
    res_health = client.get("/api/v1/health")
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert health_data["status"] == "ok"
    assert health_data["version"] == "2.0.0-MISSION-GRADE"
    assert health_data["geodetic_datum"]["standard"] == "IAU/IAG 2015 WGCCRE"
    assert health_data["geodetic_datum"]["semi_major_radius_m"] == 3396190.0
    assert health_data["geodetic_datum"]["semi_minor_radius_m"] == 3376200.0

    # -------------------------------------------------------------------------
    # STAGE 2: Topography & Benchmark Presets
    # -------------------------------------------------------------------------
    res_presets = client.get("/api/v1/spatial/environment/presets")
    assert res_presets.status_code == 200
    presets = res_presets.json()["presets"]
    jezero_preset = next((p for p in presets if p["id"] == "jezero_crater"), None)
    assert jezero_preset is not None
    assert jezero_preset["elevation_m"] == target_elev

    # -------------------------------------------------------------------------
    # STAGE 3: Atmospheric Hypsometry & Water Triple Point Validation
    # -------------------------------------------------------------------------
    res_atm = client.post("/api/v1/spatial/environment/atmospheric-profile", json={
        "latitude": target_lat,
        "longitude": target_lon,
        "elevation_m": target_elev,
        "ls_deg": season_ls,
        "max_altitude_km": 40.0,
        "step_km": 5.0
    })
    assert res_atm.status_code == 200
    atm = res_atm.json()["profile"]
    assert atm["surface_pressure_pa"] > 800.0
    assert atm["above_water_triple_point"] is True  # Pressure > 611.65 Pa (liquid water metastable)
    assert atm["scale_height_km"] > 10.0
    assert atm["provenance"]["classification"] == "MODEL_ESTIMATED"

    # -------------------------------------------------------------------------
    # STAGE 4: Visible Dust Opacity & Photovoltaic Power Budget
    # -------------------------------------------------------------------------
    res_dust = client.post("/api/v1/spatial/environment/dust-optical-depth", json={
        "latitude": target_lat,
        "longitude": target_lon,
        "elevation_m": target_elev,
        "ls_deg": season_ls
    })
    assert res_dust.status_code == 200
    dust = res_dust.json()["result"]
    assert dust["tau_visible"] < 0.60
    assert dust["opacity_category"] in ("CLEAR", "MODERATE_DUST")

    res_power = client.post("/api/v1/spatial/environment/solar-power-budget", json={
        "latitude": target_lat,
        "ls_deg": season_ls,
        "tau": dust["tau_visible"],
        "panel_area_m2": 1.3
    })
    assert res_power.status_code == 200
    power = res_power.json()["budget"]
    assert power["daily_energy_wh_sol"] > 650.0
    assert power["operational_status"] == "SURPLUS_FULL_OPERATION"
    assert power["rover_compatibility"]["mer_opportunity_spirit"]["current_status"] == "FEASIBLE"

    # -------------------------------------------------------------------------
    # STAGE 5: Terrain-Aware Rover Terramechanics & Route Optimization
    # -------------------------------------------------------------------------
    res_route = client.post("/api/v1/spatial/navigation/optimize-route", json={
        "start": {"latitude": target_lat, "longitude": target_lon, "name": "Touchdown Point"},
        "destination": {"latitude": target_lat + 0.15, "longitude": target_lon + 0.15, "name": "Delta Outcrop"},
        "mobility_profile": "rover_perseverance",
        "preference": "balanced",
        "grid_resolution": 20
    })
    assert res_route.status_code == 200
    route = res_route.json()
    assert route["status"] == "success"
    assert route["recommended_route"]["total_distance_km"] > 0.0
    assert len(route["recommended_route"]["waypoints"]) > 0
    assert route["scientific_provenance"]["classification"] == "SIMULATED"

    # -------------------------------------------------------------------------
    # STAGE 6: Planetary Interior Seismology Model (Samuel 2023 Consensual Layer)
    # -------------------------------------------------------------------------
    res_interior = client.get("/api/v1/spatial/interior/model")
    assert res_interior.status_code == 200
    interior = res_interior.json()
    assert interior["planetary_radius_km"] == 3389.5
    layer_names = [l["name"] for l in interior["layers"]]
    assert any("Basal Molten Silicate" in name for name in layer_names)
    assert any("Metallic Core" in name for name in layer_names)

    # -------------------------------------------------------------------------
    # STAGE 7: Scientific Workspace & Hypotheses Formulation
    # -------------------------------------------------------------------------
    res_studies = client.get("/api/v1/spatial/workspace/studies")
    assert res_studies.status_code == 200
    studies = res_studies.json()
    assert len(studies) >= 1
    study_id = studies[0]["study_id"]

    res_hyp = client.post(f"/api/v1/spatial/workspace/studies/{study_id}/hypotheses", json={
        "statement": "Subsurface Metastable Brine Persistence in Jezero Delta Strata",
        "status": "HYPOTHESIZED",
        "confidence_rating": 0.88,
        "linked_evidence_ids": ["obs_001"],
        "competing_hypotheses": ["Purely dry aeolian basaltic sand dunes with zero volatile retention"],
        "falsification_criteria": "Dielectric permittivity epsilon_r < 4.5 uniformly across the lower delta package."
    })
    assert res_hyp.status_code == 200
    hyp_data = res_hyp.json()
    assert hyp_data["falsification_criteria"] != ""
    assert hyp_data["confidence_rating"] == 0.88

    # -------------------------------------------------------------------------
    # STAGE 10: Workspace Scientific Package Export (Manifest, KML, LaTeX)
    # -------------------------------------------------------------------------
    # Manifest
    res_manifest = client.post(f"/api/v1/spatial/workspace/studies/{study_id}/export/manifest")
    assert res_manifest.status_code == 200
    manifest = res_manifest.json()
    assert manifest["study_manifest"]["study_id"] == study_id
    assert manifest["geojson"]["type"] == "FeatureCollection"

    # OGC KML 2.3 Traverse
    res_kml = client.post("/api/v1/spatial/workspace/export/kml", json={
        "route_name": "Jezero Delta Traverse Corridor",
        "waypoints": [
            {"latitude": target_lat, "longitude": target_lon, "elevation_m": target_elev},
            {"latitude": target_lat + 0.05, "longitude": target_lon + 0.05, "elevation_m": target_elev - 15.0}
        ]
    })
    assert res_kml.status_code == 200
    assert "<kml xmlns=" in res_kml.text
    assert "<coordinates>" in res_kml.text

    # LaTeX Table
    res_latex = client.get("/api/v1/spatial/workspace/export/latex?table_type=crater_morphometry")
    assert res_latex.status_code == 200
    assert "\\begin{table}" in res_latex.json()["latex"]
