"""
Tests for rover mobility and traverse simulation.
Validates:
1. Multi-rover specification catalog (Perseverance, Curiosity, Opportunity, Spirit, Zhurong, ExoMars, Hexacopter, Crew Rover).
2. Regolith geotechnical database (Bekker-Wong parameters: c, phi, kc, kphi, n).
3. Daily communication windows (MRO, Odyssey, TGO, DTE).
4. Multi-rover simulation comparison across identical Martian terrain corridors.
5. Regolith sensitivity analysis (dune fields vs basaltic sand vs bedrock).
6. Diurnal insolation, dust tau optical depth attenuation, and survival heater load.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from zuhura.api.main import app
from zuhura.navigation.mobility_model import (
    ROVER_SPECIFICATIONS,
    REGOLITH_DATABASE,
    assess_terramechanics,
    compute_diurnal_insolation,
    compute_energy_consumption,
    calculate_comm_windows,
    evaluate_traverse_risks,
    simulate_multi_rover_comparison,
)


@pytest.mark.asyncio
async def test_get_mobility_profiles_and_specifications():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/spatial/navigation/profiles")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "operational"
        assert "profiles" in data
        assert "specifications" in data

        specs = data["specifications"]
        # Verify all major rovers are cataloged
        expected_rovers = [
            "rover_perseverance",
            "rover_curiosity",
            "rover_opportunity",
            "rover_spirit",
            "rover_zhurong",
            "rover_exomars",
            "crew_traverser",
            "scout_hexacopter",
        ]
        for r_id in expected_rovers:
            assert r_id in specs
            rover = specs[r_id]
            assert rover["mass_kg"] > 0
            assert rover["max_safe_slope_deg"] > 0
            assert rover["power_source"] in ("mmrtg", "solar_pv", "fuel_cell", "battery")


@pytest.mark.asyncio
async def test_get_regolith_geotechnical_types():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/spatial/navigation/regolith-types")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "operational"
        regolith = data["regolith_types"]

        assert "basaltic_sand" in regolith
        assert "compact_dust" in regolith
        assert "duricrust" in regolith
        assert "bedrock" in regolith
        assert "dune_fields" in regolith

        # Validate Bekker parameters
        sand = regolith["basaltic_sand"]
        assert sand["cohesion_kpa"] == 0.2
        assert sand["internal_friction_deg"] == 35.0
        assert sand["sinkage_modulus_kc"] > 0
        assert sand["sinkage_exponent_n"] > 0


@pytest.mark.asyncio
async def test_get_communication_windows():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/spatial/navigation/comm-windows",
            json={"latitude": 18.38, "longitude": 77.58}
        )
        assert resp.status_code == 200
        passes = resp.json()
        assert len(passes) >= 4

        targets = [p["target"] for p in passes]
        assert "MRO" in targets
        assert "ODYSSEY" in targets
        assert "TGO" in targets

        for p in passes:
            assert p["duration_minutes"] > 5.0
            assert p["max_elevation_deg"] > 15.0
            assert p["data_capacity_mbit"] > 0.0


@pytest.mark.asyncio
async def test_multi_rover_simulation_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "start_latitude": 18.38,
            "start_longitude": 77.58,
            "destination_latitude": 18.44,
            "destination_longitude": 77.45,
            "rovers": [
                "rover_perseverance",
                "rover_curiosity",
                "rover_opportunity",
                "rover_zhurong",
                "scout_hexacopter",
                "crew_traverser"
            ],
            "soil_type": "basaltic_sand",
            "solar_longitude_ls": 180.0,
            "dust_optical_depth_tau": 0.5
        }
        resp = await client.post("/api/v1/spatial/navigation/multi-rover-simulation", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["status"] == "success"
        assert "corridor_summary" in data
        assert data["corridor_summary"]["distance_km"] > 0.0

        results = data["comparison_results"]
        assert len(results) == 6

        # Check Perseverance vs Opportunity
        perseverance = next(r for r in results if r["rover_id"] == "rover_perseverance")
        opportunity = next(r for r in results if r["rover_id"] == "rover_opportunity")
        hexacopter = next(r for r in results if r["rover_id"] == "scout_hexacopter")

        # Perseverance travels faster than Opportunity
        assert perseverance["total_sols_required"] <= opportunity["total_sols_required"]
        # Hexacopter has zero sinkage and zero wheel slip
        assert hexacopter["max_wheel_slip_pct"] == 0.0
        assert hexacopter["mean_sinkage_cm"] == 0.0

        # Provenance epistemic validation
        assert data["scientific_provenance"]["classification"] == "SIMULATED"


def test_bekker_terramechanics_across_regolith_types():
    perseverance = ROVER_SPECIFICATIONS["rover_perseverance"]

    sand_metrics = assess_terramechanics(slope_deg=8.0, roughness_tri=1.5, vehicle=perseverance, soil_type="basaltic_sand")
    dune_metrics = assess_terramechanics(slope_deg=8.0, roughness_tri=1.5, vehicle=perseverance, soil_type="dune_fields")
    bedrock_metrics = assess_terramechanics(slope_deg=8.0, roughness_tri=1.5, vehicle=perseverance, soil_type="bedrock")

    # Dunes produce higher slip and higher sinkage than basaltic sand
    assert dune_metrics.estimated_wheel_slip_pct > sand_metrics.estimated_wheel_slip_pct
    assert dune_metrics.sinkage_depth_cm > sand_metrics.sinkage_depth_cm

    # Bedrock produces minimal sinkage and minimal slip
    assert bedrock_metrics.sinkage_depth_cm < 1.0
    assert bedrock_metrics.estimated_wheel_slip_pct < 10.0


def test_diurnal_insolation_and_dust_tau_attenuation():
    # Clear Martian sky (tau = 0.3) vs severe regional dust storm (tau = 2.5)
    flux_clear, temp_clear = compute_diurnal_insolation(lat_deg=0.0, ls_deg=180.0, dust_tau=0.3, local_hour_lmst=12.0)
    flux_dust, temp_dust = compute_diurnal_insolation(lat_deg=0.0, ls_deg=180.0, dust_tau=2.5, local_hour_lmst=12.0)

    assert flux_clear > 400.0  # Strong midday solar flux
    assert flux_dust < flux_clear * 0.4  # Dust dramatically attenuates beam

    # Solar rover energy budget under dust storm
    opportunity = ROVER_SPECIFICATIONS["rover_opportunity"]
    energy_clear = compute_energy_consumption(
        distance_km=0.5,
        elevation_gain_m=10.0,
        mean_slope_deg=4.0,
        duration_hours=3.0,
        vehicle=opportunity,
        dust_tau=0.3
    )
    energy_dust = compute_energy_consumption(
        distance_km=0.5,
        elevation_gain_m=10.0,
        mean_slope_deg=4.0,
        duration_hours=3.0,
        vehicle=opportunity,
        dust_tau=2.5
    )

    assert energy_clear.solar_energy_available_wh > energy_dust.solar_energy_available_wh
    assert energy_dust.battery_net_delta_wh < 0.0  # Severe battery deficit during dust storm
