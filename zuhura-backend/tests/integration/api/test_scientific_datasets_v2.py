"""
Zuhura Backend - Test Suite for NASA & USGS Scientific Datasets Upgrades
Validates endpoints for:
1. NASA Mars Trek layers catalog (/api/v1/catalog/trek)
2. USGS SIM 3292 Geology catalog (/api/v1/catalog/geology)
3. Mars Craters and Impact Basins catalog (/api/v1/catalog/craters)
4. Curiosity Proposed Path up Mount Sharp (/api/v1/mount-sharp)
5. Mars 2020 Perseverance Raw Images & Telemetry (/api/v1/rover/raw-images, /api/v1/rover/stats)
6. Mars 3D Verified Rover Traverses (/api/v1/rover/traverses/{rover})
7. Mars Trek WMTS Tile Caching Proxy (/api/v1/tiles/trek/...)
"""

import pytest
from httpx import AsyncClient, ASGITransport
from zuhura.api.main import app


@pytest.mark.asyncio
async def test_mount_sharp_metadata_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/mount-sharp")
        assert resp.status_code == 200
        data = resp.json()
        assert data["dataset_id"] == "NASA-MSL-PIA23179-MOUNT-SHARP"
        assert "Gale Crater" in data["target"]
        assert len(data["geological_units"]) >= 5
        assert "HiRISE" in [inst["instrument"] for inst in data["contributing_instruments"]]
        assert "download_links" in data
        assert data["download_links"]["original_tiff"] == "/api/v1/mount-sharp/assets/PIA23179.tif"


@pytest.mark.asyncio
async def test_mount_sharp_asset_serving():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/mount-sharp/assets/PIA23179.jpg")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/jpeg"
        assert len(resp.content) > 100000


@pytest.mark.asyncio
async def test_rover_raw_images_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/rover/raw-images?limit=6")
        assert resp.status_code == 200
        data = resp.json()
        assert data["rover"] == "perseverance"
        assert data["total"] >= 10
        assert len(data["items"]) <= 6
        item = data["items"][0]
        assert "image_id" in item
        assert "camera_name" in item
        assert "sol" in item
        assert item["original_url"].startswith("http")


@pytest.mark.asyncio
async def test_rover_raw_images_camera_filtering():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/rover/raw-images?camera=mastcam_z")
        assert resp.status_code == 200
        data = resp.json()
        for it in data["items"]:
            assert it["instrument"] == "mastcam_z" or it["camera_code"] in ["MCZ_RIGHT", "MCZ_LEFT"]


@pytest.mark.asyncio
async def test_rover_traverses_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Perseverance
        resp_m20 = await client.get("/api/v1/rover/traverses/perseverance")
        assert resp_m20.status_code == 200
        geo_m20 = resp_m20.json()
        assert geo_m20["type"] == "FeatureCollection"
        assert len(geo_m20["features"]) > 50

        # Curiosity
        resp_msl = await client.get("/api/v1/rover/traverses/curiosity")
        assert resp_msl.status_code == 200
        geo_msl = resp_msl.json()
        assert geo_msl["type"] == "FeatureCollection"
        assert len(geo_msl["features"]) > 100


@pytest.mark.asyncio
async def test_rover_stats_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/rover/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["active_missions"]) >= 2
        rovers = [m["rover"] for m in data["active_missions"]]
        assert any("Perseverance" in r for r in rovers)
        assert any("Curiosity" in r for r in rovers)


@pytest.mark.asyncio
async def test_catalog_mars_trek_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/catalog/trek?page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 140
        assert len(data["layers"]) <= 10
        layer = data["layers"][0]
        assert "label" in layer
        assert "wmts_template" in layer
        assert "trek.nasa.gov" in layer["wmts_template"]


@pytest.mark.asyncio
async def test_catalog_geology_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/catalog/geology")
        assert resp.status_code == 200
        data = resp.json()
        assert data["dataset_id"] == "USGS-SIM-3292-MARS-GEOLOGY"
        assert len(data["chronostratigraphic_units"]) >= 8
        assert "Tanaka" in data["authors"]


@pytest.mark.asyncio
async def test_catalog_craters_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/catalog/craters?min_diameter_km=100")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 3
        names = [c["name"] for c in data["craters"]]
        assert "Hellas Planitia" in names
        assert "Gale Crater" in names
