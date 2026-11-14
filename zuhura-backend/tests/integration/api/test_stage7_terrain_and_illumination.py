"""
Zuhura Backend - Stage 7 Multi-Resolution Terrain & Illumination Tests
Tests:
  1. GET /api/v1/tiles/terrain/global/layer.json
  2. GET /api/v1/tiles/terrain/global/0/0/0.terrain (MIME type, 88-byte header, octvertexnormals)
  3. Regional terrain endpoints: Gale, Olympus Mons, Valles Marineris
  4. GET /api/v1/illumination/solar-position (interactive mode)
  5. GET /api/v1/illumination/solar-position (physical ephemeris mode)
"""

import pytest
from httpx import ASGITransport, AsyncClient
from zuhura.api.main import app
from zuhura_data.terrain.quantized_mesh import decode_quantized_mesh


@pytest.mark.asyncio
async def test_global_terrain_layer_json():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/tiles/terrain/global/layer.json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["format"] == "quantized-mesh-1.0"
        assert data["scheme"] == "tms"
        assert data["bounds"] == [-180.0, -90.0, 180.0, 90.0]
        assert "octvertexnormals" in data["extensions"]
        assert len(data["available"]) >= 3  # Levels 0, 1, 2


@pytest.mark.asyncio
async def test_global_terrain_binary_tile_and_normals():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/tiles/terrain/global/0/0/0.terrain")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/vnd.quantized-mesh"
        assert len(resp.content) >= 88

        # Decode using full parser
        info = decode_quantized_mesh(resp.content)
        assert info["vertex_count"] == 1089  # 33x33
        assert info["triangle_count"] == 2048
        assert any(ext["type"] == "octvertexnormals" for ext in info["extensions"])


@pytest.mark.asyncio
async def test_regional_terrain_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for reg in ["gale", "valles_marineris", "olympus_mons"]:
            resp = await client.get(f"/api/v1/tiles/terrain/{reg}/layer.json")
            assert resp.status_code == 200
            data = resp.json()
            assert data["format"] == "quantized-mesh-1.0"
            assert data["scheme"] == "tms"
            assert "octvertexnormals" in data["extensions"]


@pytest.mark.asyncio
async def test_illumination_interactive_mode():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Request interactive lighting with azimuth=315, elevation=45 over Jezero
        resp = await client.get("/api/v1/illumination/solar-position?latitude=18.38&longitude=77.58&azimuth_override=315.0&elevation_override=45.0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "interactive_visualization"
        assert data["solar_azimuth_deg"] == 315.0
        assert data["solar_elevation_deg"] == 45.0
        assert data["is_illuminated"] is True
        assert len(data["sun_direction_mcmf"]) == 3
        assert len(data["sun_direction_enu"]) == 3


@pytest.mark.asyncio
async def test_illumination_physical_ephemeris_mode():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Request physical solar position for southern summer (Ls=270) at local noon (t=12.0)
        resp = await client.get("/api/v1/illumination/solar-position?latitude=-14.0&longitude=285.0&solar_longitude_ls=270.0&solar_time_hours=12.0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "solar_ephemeris_model"
        assert data["solar_longitude_ls"] == 270.0
        assert data["local_solar_time_hours"] == 12.0
        assert data["is_illuminated"] is True
        assert data["solar_elevation_deg"] > 70.0  # Sun high overhead at noon in summer
