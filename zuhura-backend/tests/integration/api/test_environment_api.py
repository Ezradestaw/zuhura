"""
Integration tests for the environment API.
"""

import pytest
from fastapi.testclient import TestClient
from zuhura.api.main import app

client = TestClient(app)


def test_orbital_overview():
    """Validates Mars orbital mechanics, insolation, and seasonal datum pressure variation."""
    # Test Ls = 71 (near aphelion, maximum distance from Sun)
    res_aph = client.get("/api/v1/spatial/environment/overview?ls_deg=71.0")
    assert res_aph.status_code == 200
    data_aph = res_aph.json()
    assert data_aph["status"] == "success"
    assert data_aph["orbital"]["heliocentric_distance_au"] > 1.6
    assert data_aph["orbital"]["top_of_atmosphere_solar_flux_w_m2"] < 520.0

    # Test Ls = 251 (near perihelion, minimum distance from Sun)
    res_peri = client.get("/api/v1/spatial/environment/overview?ls_deg=251.0")
    assert res_peri.status_code == 200
    data_peri = res_peri.json()
    assert data_peri["orbital"]["heliocentric_distance_au"] < 1.40
    assert data_peri["orbital"]["top_of_atmosphere_solar_flux_w_m2"] > 700.0

    # Solar constant at perihelion must exceed aphelion
    assert data_peri["orbital"]["top_of_atmosphere_solar_flux_w_m2"] > data_aph["orbital"]["top_of_atmosphere_solar_flux_w_m2"]

    # Datum pressure must fluctuate between ~600 Pa and ~900 Pa
    assert 600.0 <= data_aph["mean_datum_pressure_pa"] <= 900.0
    assert 600.0 <= data_peri["mean_datum_pressure_pa"] <= 900.0


def test_site_presets():
    """Validates retrieval of canonical planetary benchmark presets."""
    res = client.get("/api/v1/spatial/environment/presets")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["count"] >= 5

    preset_ids = [p["id"] for p in data["presets"]]
    assert "jezero_crater" in preset_ids
    assert "olympus_mons_caldera" in preset_ids
    assert "hellas_planitia_basin" in preset_ids


def test_vertical_atmospheric_profile_olympus_vs_hellas():
    """
    Validates hydrostatic barometric hypsometry across extreme Martian elevations.
    Olympus Mons summit (+21.2 km) vs Hellas Planitia floor (-7.1 km).
    """
    # Olympus Mons Summit (extreme altitude)
    res_olympus = client.post("/api/v1/spatial/environment/atmospheric-profile", json={
        "latitude": 18.65,
        "longitude": 226.20,
        "elevation_m": 21229.0,
        "ls_deg": 0.0,
        "max_altitude_km": 40.0,
        "step_km": 5.0
    })
    assert res_olympus.status_code == 200
    prof_olympus = res_olympus.json()["profile"]
    assert prof_olympus["surface_pressure_pa"] < 150.0  # Ultra-thin atmosphere
    assert prof_olympus["above_water_triple_point"] is False
    assert prof_olympus["scale_height_km"] > 9.0
    assert len(prof_olympus["layers"]) > 5

    # Hellas Planitia Basin Floor (deepest depression)
    res_hellas = client.post("/api/v1/spatial/environment/atmospheric-profile", json={
        "latitude": -42.70,
        "longitude": 70.00,
        "elevation_m": -7152.0,
        "ls_deg": 180.0,
        "max_altitude_km": 40.0,
        "step_km": 5.0
    })
    assert res_hellas.status_code == 200
    prof_hellas = res_hellas.json()["profile"]
    assert prof_hellas["surface_pressure_pa"] > 1000.0  # Above 10 mbar
    assert prof_hellas["above_water_triple_point"] is True  # > 611.65 Pa (liquid water metastable!)

    # Density at Hellas floor must be significantly higher than at Olympus summit
    assert prof_hellas["surface_density_kg_m3"] > 5.0 * prof_olympus["surface_density_kg_m3"]

    # Provenance record check
    assert prof_hellas["provenance"]["classification"] == "MODEL_ESTIMATED"
    assert "MCD" in prof_hellas["provenance"]["original_dataset_id"]


def test_dust_optical_depth_climatology():
    """Validates seasonal and geographic visible dust optical depth and risk classification."""
    # Clear Northern Spring at Jezero
    res_clear = client.post("/api/v1/spatial/environment/dust-optical-depth", json={
        "latitude": 18.38,
        "longitude": 77.58,
        "elevation_m": -2500.0,
        "ls_deg": 60.0,
        "global_dust_multiplier": 1.0
    })
    assert res_clear.status_code == 200
    dust_clear = res_clear.json()["result"]
    assert dust_clear["tau_visible"] < 0.45
    assert dust_clear["opacity_category"] == "CLEAR"
    assert dust_clear["direct_transmission_zenith"] > 0.60
    assert len(dust_clear["operational_recommendations"]) >= 2

    # Global Dust Storm Scenario (tau elevated)
    res_storm = client.post("/api/v1/spatial/environment/dust-optical-depth", json={
        "latitude": -35.0,
        "longitude": 70.0,
        "elevation_m": -6000.0,
        "ls_deg": 260.0,
        "global_dust_multiplier": 3.0
    })
    assert res_storm.status_code == 200
    dust_storm = res_storm.json()["result"]
    assert dust_storm["tau_visible"] > 2.2
    assert dust_storm["opacity_category"] in ("REGIONAL_STORM", "GLOBAL_ENCIRCLEMENT")
    assert dust_storm["dust_storm_risk_index"] > 0.70
    assert dust_storm["is_basin_amplified"] is True


def test_diurnal_temperature_cycle():
    """Validates 24-hour diurnal thermal cycle, thermal inertia damping, and CO2 frost boundary."""
    # Low thermal inertia (fine dust)
    res_dust = client.post("/api/v1/spatial/environment/diurnal-temperature", json={
        "latitude": 0.0,
        "elevation_m": 0.0,
        "ls_deg": 0.0,
        "thermal_inertia_tiu": 80.0,
        "albedo": 0.25,
        "tau": 0.35
    })
    assert res_dust.status_code == 200
    thermal_dust = res_dust.json()["profile"]
    assert len(thermal_dust["hourly_curve"]) == 24
    assert thermal_dust["diurnal_temperature_swing_k"] > 60.0  # Large swing for fine dust

    # High thermal inertia (competent bedrock)
    res_rock = client.post("/api/v1/spatial/environment/diurnal-temperature", json={
        "latitude": 0.0,
        "elevation_m": 0.0,
        "ls_deg": 0.0,
        "thermal_inertia_tiu": 700.0,
        "albedo": 0.15,
        "tau": 0.35
    })
    assert res_rock.status_code == 200
    thermal_rock = res_rock.json()["profile"]

    # High thermal inertia reduces diurnal swing
    assert thermal_rock["diurnal_temperature_swing_k"] < thermal_dust["diurnal_temperature_swing_k"]
    assert "Bedrock" in thermal_rock["regolith_type"] or "Competent" in thermal_rock["regolith_type"]


def test_solar_power_budget():
    """Validates solar insolation power budgeting and rover feasibility status."""
    # Nominal clear conditions
    res_nominal = client.post("/api/v1/spatial/environment/solar-power-budget", json={
        "latitude": 18.38,
        "ls_deg": 180.0,
        "tau": 0.35,
        "panel_area_m2": 1.3,
        "cell_efficiency": 0.295,
        "dust_deposition_factor": 0.90
    })
    assert res_nominal.status_code == 200
    budget_nominal = res_nominal.json()["budget"]
    assert budget_nominal["daily_energy_wh_sol"] > 700.0
    assert budget_nominal["operational_status"] == "SURPLUS_FULL_OPERATION"
    assert budget_nominal["rover_compatibility"]["mer_opportunity_spirit"]["current_status"] == "FEASIBLE"
    assert len(budget_nominal["hourly_power_w"]) == 24

    # Severe dust storm conditions
    res_storm = client.post("/api/v1/spatial/environment/solar-power-budget", json={
        "latitude": 18.38,
        "ls_deg": 260.0,
        "tau": 3.5,
        "panel_area_m2": 1.3,
        "cell_efficiency": 0.295,
        "dust_deposition_factor": 0.50
    })
    assert res_storm.status_code == 200
    budget_storm = res_storm.json()["budget"]
    assert budget_storm["daily_energy_wh_sol"] < 250.0
    assert budget_storm["operational_status"] in ("CRITICAL_SURVIVAL_ONLY", "ENERGY_DEFICIT_HAZARD")


def test_mission_environment_assessment():
    """Validates end-to-end composite environmental health report for Jezero Crater."""
    res = client.post("/api/v1/spatial/environment/mission-assessment", json={
        "target_name": "Jezero Crater Science Zone",
        "latitude": 18.38,
        "longitude": 77.58,
        "elevation_m": -2500.0,
        "ls_deg": 180.0,
        "thermal_inertia_tiu": 350.0,
        "panel_area_m2": 1.3
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assessment = data["assessment"]
    assert assessment["target_name"] == "Jezero Crater Science Zone"
    assert 0.0 <= assessment["overall_site_viability_score"] <= 100.0
    assert "orbital" in assessment
    assert "atmosphere" in assessment
    assert "dust" in assessment
    assert "thermal" in assessment
    assert "power_budget" in assessment
    assert assessment["provenance"]["classification"] == "MODEL_ESTIMATED"
