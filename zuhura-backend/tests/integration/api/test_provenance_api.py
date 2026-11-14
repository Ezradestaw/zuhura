"""
Zuhura Planetary Digital Twin - Scientific Truth Engine Provenance API Tests
Verifies epistemic classifications, uncertainty models, and competing model reconciliations.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from zuhura.api.main import app


@pytest.mark.asyncio
async def test_get_epistemic_classifications():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/provenance/classifications")
    assert res.status_code == 200
    data = res.json()
    ids = [c["id"] for c in data["classifications"]]
    assert "OBSERVED" in ids
    assert "MEASURED" in ids
    assert "DERIVED" in ids
    assert "MODEL_ESTIMATED" in ids
    assert "SIMULATED" in ids
    assert "PROVISIONAL" in ids
    assert "UNVERIFIED" in ids


@pytest.mark.asyncio
async def test_get_all_dataset_provenance():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/provenance/datasets")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["geodetic_datum"] == "IAU/IAG 2015 WGCCRE"
    assert data["vertical_datum"] == "Mars Areoid (MOLA GMM-3 / MEG128)"
    assert data["total_records"] >= 7
    # Verify records have required fields
    for rec in data["records"]:
        assert "classification" in rec
        assert "original_dataset_id" in rec
        assert "spatial_resolution" in rec
        assert "measurement_units" in rec


@pytest.mark.asyncio
async def test_get_specific_dataset_provenance():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/provenance/datasets/MOLA")
    assert res.status_code == 200
    data = res.json()
    assert data["classification"] == "MEASURED"
    assert data["original_dataset_id"] == "MOLA_MEG128"
    assert data["uncertainty"]["uncertainty_absolute"] == 1.0
    assert data["uncertainty"]["unit"] == "meters"


@pytest.mark.asyncio
async def test_get_competing_models():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/provenance/competing-models")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["comparisons"]) >= 2
    insight = data["comparisons"][0]
    assert "Mars Core Radius" in insight["subject"]
    model_ids = [m["model_id"] for m in insight["competing_interpretations"]]
    assert "stahler_2021" in model_ids
    assert "samuel_khan_2023" in model_ids


@pytest.mark.asyncio
async def test_create_computation_manifest():
    transport = ASGITransport(app=app)
    payload = {
        "algorithm_name": "horn_slope",
        "algorithm_version": "v1.4",
        "inputs": {"latitude": 18.38, "longitude": 77.58, "kernel": 3},
        "outputs": {"slope_deg": 4.2, "roughness_tri": 1.1},
        "duration_ms": 12.5
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/provenance/manifest", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "COMP_HORN_SLOPE_" in data["computation_id"]
    assert data["input_parameters_hash"] is not None
    assert data["output_summary_hash"] is not None
    assert data["provenance"]["classification"] == "DERIVED"