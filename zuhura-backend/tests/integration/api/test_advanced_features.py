"""
Integration tests for Advanced Zuhura Mars features:
- X-Ray Mars (Planetary Interior)
- Optimize Navigation (Terrain-Aware Route Planning)
- Hover Intelligence (Contextual Cursor Inspection)
- Location Pinpoint (Landscape Image Localization)
- Mars Region Discovery (Geological Segmentation)
"""

import pytest
from httpx import AsyncClient, ASGITransport
from zuhura.api.main import app


@pytest.mark.asyncio
async def test_optimize_navigation_route():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Route from Jezero floor to western delta fan
        payload = {
            "start": {"latitude": 18.38, "longitude": 77.58, "name": "Perseverance Landing Site"},
            "destination": {"latitude": 18.44, "longitude": 77.45, "name": "Kodiak Butte Delta Front"},
            "mobility_profile": "rover_perseverance",
            "preference": "minimum_slope",
            "grid_resolution": 20
        }
        resp = await client.post("/api/v1/spatial/navigation/optimize-route", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        rec = data["recommended_route"]
        assert rec["total_distance_km"] > 0.0
        assert len(rec["waypoints"]) >= 10
        assert len(rec["segments"]) >= 9
        assert "geojson" in rec
        assert rec["geojson"]["type"] == "FeatureCollection"
        assert "max_slope_degrees" in rec
        assert rec["max_slope_degrees"] >= 0.0
        # Alternative routes present
        assert len(data["alternative_routes"]) >= 1


@pytest.mark.asyncio
async def test_hover_intelligence_inspect():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Hover near Jezero Crater
        resp = await client.get("/api/v1/spatial/hover/inspect?lat=18.38&lon=77.58")
        assert resp.status_code == 200
        data = resp.json()
        assert data["latitude"] == 18.38
        assert data["longitude"] == 77.58
        assert "elevation_m" in data
        assert "geological_era" in data
        assert "nearest_feature" in data
        assert "Jezero" in data["nearest_feature"]["name"]
        assert data["imagery_coverage"]["viking_global_232m"] is True
        assert data["imagery_coverage"]["ctx_regional_5m"] is True


@pytest.mark.asyncio
async def test_location_pinpoint_matching():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create a mock JPEG binary payload
        mock_image = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb" + (b"\xaa" * 1024)
        files = {
            "file": ("mars_test.jpg", mock_image, "image/jpeg")
        }
        data = {
            "mission_hint": "Perseverance",
            "approx_lat": 18.4,
            "approx_lon": 77.5
        }
        resp = await client.post("/api/v1/spatial/pinpoint/analyze-image", files=files, data=data)
        assert resp.status_code == 200
        res = resp.json()
        assert res["candidates_found"] > 0
        assert len(res["candidates"]) >= 1
        top = res["top_candidate"]
        assert top is not None
        assert "latitude" in top
        assert "longitude" in top
        assert 0.0 <= top["similarity_score"] <= 1.0
        assert top["confidence_level"] in ("high", "medium", "low", "insufficient_evidence")


@pytest.mark.asyncio
async def test_region_discovery_segmentation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "center_latitude": 18.38,
            "center_longitude": 77.58,
            "search_radius_km": 50.0,
            "min_region_area_km2": 25.0
        }
        resp = await client.post("/api/v1/spatial/regions/discover", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["total_regions_discovered"] >= 2
        for r in data["regions"]:
            assert r["naming_status"] == "PROVISIONAL_PLATFORM_GENERATED"
            assert "Provisional" in r["name"]
            assert len(r["boundary_polygon"]) >= 5
            # Verify closed polygon ring
            assert r["boundary_polygon"][0]["latitude"] == r["boundary_polygon"][-1]["latitude"]
            assert r["surface_area_km2"] > 0.0
        assert data["geojson"]["type"] == "FeatureCollection"
