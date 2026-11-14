"""
Integration tests for the terrain analysis API.
Validates all 4 REST endpoints under /api/v1/spatial/terrain/*:
  1. POST /api/v1/spatial/terrain/point-analysis
  2. POST /api/v1/spatial/terrain/profile
  3. POST /api/v1/spatial/terrain/statistics
  4. POST /api/v1/spatial/terrain/compare
"""

import pytest
from httpx import ASGITransport, AsyncClient
from zuhura.api.main import app


@pytest.mark.asyncio
async def test_point_analysis_valid_jezero():
    """Verify point analysis at Jezero Crater floor returns accurate elevation, slope, and aspect."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/spatial/terrain/point-analysis",
            json={
                "latitude": 18.38,
                "longitude": 77.58,
                "kernel_size": 3,
                "include_morphometry": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()

        # Coordinate conventions
        assert data["coordinate"]["latitude"] == 18.38
        assert data["coordinate"]["longitude"] == 77.58
        assert data["coordinate"]["latitude_type"] == "planetocentric"
        assert data["coordinate"]["longitude_convention"] == "east_positive"

        # Elevation and datum
        assert -2700.0 <= data["elevation"]["elevation_m"] <= -2500.0
        assert "MOLA" in data["elevation"]["vertical_datum"]
        assert data["elevation"]["nodata_status"] is False

        # Derivatives
        assert "slope_deg" in data["derivatives"]
        assert 0.0 <= data["derivatives"]["slope_deg"] <= 15.0
        assert 0.0 <= data["derivatives"]["aspect_deg"] <= 360.0
        assert data["derivatives"]["calculation_method"].startswith("Horn (1981)")

        # Morphometry
        assert data["morphometry"] is not None
        assert data["morphometry"]["tpi_classification"] in [
            "flat_plain",
            "lower_slope_or_depression",
            "upper_slope",
            "ridge_crest",
            "canyon_or_pit",
        ]

        # Provenance
        assert "mola" in data["provenance"]["source_dataset"].lower()
        assert data["provenance"]["validation_status"] == "scientifically_validated"


@pytest.mark.asyncio
async def test_point_analysis_olympus_mons_peak():
    """Verify point analysis at Olympus Mons summit handles extreme elevations without overflow."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/spatial/terrain/point-analysis",
            json={
                "latitude": 18.65,
                "longitude": 226.2,
                "kernel_size": 3,
                "include_morphometry": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["elevation"]["elevation_m"] > 20000.0
        assert data["derivatives"]["slope_deg"] >= 0.0


@pytest.mark.asyncio
async def test_point_analysis_negative_longitude_normalization():
    """Verify that west longitudes (e.g. -133.8°E = 226.2°E) normalize transparently."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/spatial/terrain/point-analysis",
            json={"latitude": 18.65, "longitude": -133.8, "kernel_size": 3},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert abs(data["coordinate"]["longitude"] - 226.2) < 0.05
        assert data["elevation"]["elevation_m"] > 20000.0


@pytest.mark.asyncio
async def test_point_analysis_polar_fallback():
    """Verify that high-latitude query (|lat| > 88°) switches to polar stereographic fallback."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/spatial/terrain/point-analysis",
            json={"latitude": 89.5, "longitude": 45.0, "kernel_size": 3},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["elevation"]["elevation_m"] is not None
        assert "polar" in data["provenance"]["validation_status"]


@pytest.mark.asyncio
async def test_point_analysis_invalid_inputs():
    """Verify 422 Unprocessable Entity on out-of-bounds latitude or invalid kernel size."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Latitude out of bounds
        resp1 = await client.post(
            "/api/v1/spatial/terrain/point-analysis",
            json={"latitude": 95.0, "longitude": 0.0},
        )
        assert resp1.status_code == 422

        # Invalid even kernel size
        resp2 = await client.post(
            "/api/v1/spatial/terrain/point-analysis",
            json={"latitude": 0.0, "longitude": 0.0, "kernel_size": 4},
        )
        assert resp2.status_code == 422


@pytest.mark.asyncio
async def test_transect_profile_jezero_rim_to_floor():
    """Verify great-circle transect profile across Jezero Crater."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/spatial/terrain/profile",
            json={
                "start_point": {"latitude": 18.25, "longitude": 77.35},
                "end_point": {"latitude": 18.50, "longitude": 77.80},
                "num_samples": 20,
                "include_derivatives": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()

        summary = data["transect_summary"]
        assert summary["num_samples"] == 20
        assert summary["total_distance_km"] > 25.0
        assert summary["min_elevation_m"] < summary["max_elevation_m"]
        assert summary["cumulative_elevation_gain_m"] >= 0.0
        assert summary["cumulative_elevation_loss_m"] >= 0.0

        samples = data["samples"]
        assert len(samples) == 20
        # Check monotonic distance accumulation
        for i in range(1, len(samples)):
            assert samples[i]["distance_km"] > samples[i - 1]["distance_km"]
            assert "segment_slope_deg" in samples[i]


@pytest.mark.asyncio
async def test_transect_profile_sample_count_limits():
    """Verify 422 validation on sample count out of bounds (allowed 5 to 500)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Too low
        resp1 = await client.post(
            "/api/v1/spatial/terrain/profile",
            json={
                "start_point": {"latitude": 0.0, "longitude": 0.0},
                "end_point": {"latitude": 1.0, "longitude": 1.0},
                "num_samples": 2,
            },
        )
        assert resp1.status_code == 422

        # Too high
        resp2 = await client.post(
            "/api/v1/spatial/terrain/profile",
            json={
                "start_point": {"latitude": 0.0, "longitude": 0.0},
                "end_point": {"latitude": 1.0, "longitude": 1.0},
                "num_samples": 600,
            },
        )
        assert resp2.status_code == 422


@pytest.mark.asyncio
async def test_area_statistics_jezero():
    """Verify local morphometric statistics across a 15 km radius circular footprint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/spatial/terrain/statistics",
            json={
                "center_point": {"latitude": 18.38, "longitude": 77.58},
                "radius_km": 15.0,
            },
        )
        assert resp.status_code == 200
        data = resp.json()

        # Region definition
        assert data["query_region"]["type"] == "circle"
        assert data["query_region"]["radius_km"] == 15.0
        assert data["query_region"]["area_km2"] > 700.0

        # Elevation statistics
        elev_stats = data["elevation_statistics"]
        assert elev_stats["cell_count"] > 3000
        assert elev_stats["min_m"] < elev_stats["max_m"]
        assert elev_stats["relief_m"] == round(elev_stats["max_m"] - elev_stats["min_m"], 1)

        # Slope statistics
        slope_stats = data["slope_statistics"]
        assert 0.0 <= slope_stats["mean_deg"] <= slope_stats["max_deg"]
        assert slope_stats["trafficability_grade"] in [
            "low_slope_favorable",
            "moderate_slope_negotiable",
            "steep_hazardous",
            "extreme_inaccessible",
        ]

        # Roughness indices
        rough = data["roughness_indices"]
        assert rough["mean_tri_m"] >= 0.0
        assert 0.0 <= rough["vector_ruggedness_measure"] <= 1.0


@pytest.mark.asyncio
async def test_area_statistics_radius_bounds():
    """Verify radius bounds validation (0.1 to 250 km)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp1 = await client.post(
            "/api/v1/spatial/terrain/statistics",
            json={"center_point": {"latitude": 0.0, "longitude": 0.0}, "radius_km": 0.05},
        )
        assert resp1.status_code == 422

        resp2 = await client.post(
            "/api/v1/spatial/terrain/statistics",
            json={"center_point": {"latitude": 0.0, "longitude": 0.0}, "radius_km": 300.0},
        )
        assert resp2.status_code == 422


@pytest.mark.asyncio
async def test_terrain_compare_jezero_vs_gale():
    """Verify head-to-head comparison between Jezero Crater and Gale Crater."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/spatial/terrain/compare",
            json={
                "site_a": {"latitude": 18.38, "longitude": 77.58},
                "site_b": {"latitude": -5.37, "longitude": 137.81},
                "name_a": "Jezero Crater Floor",
                "name_b": "Gale Crater Mount Sharp Base",
            },
        )
        assert resp.status_code == 200
        data = resp.json()

        # Separation
        sep = data["separation"]
        assert 3500.0 <= sep["great_circle_distance_km"] <= 4000.0
        assert sep["elevation_delta_m"] is not None
        assert sep["net_gradient_percent"] >= 0.0
        assert sep["site_b_relative_to_a"] in ["higher", "lower", "equivalent"]

        # Comparison matrix
        matrix = data["comparison_matrix"]
        assert matrix["site_a"]["name"] == "Jezero Crater Floor"
        assert matrix["site_b"]["name"] == "Gale Crater Mount Sharp Base"
        assert matrix["site_a"]["elevation_m"] is not None
        assert matrix["site_b"]["elevation_m"] is not None

        # Provenance
        assert "vertical_datum" in data["provenance"]
        assert data["provenance"]["validation_status"] == "scientifically_validated"
