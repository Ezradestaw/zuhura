import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch

from zuhura.api.main import app
from zuhura.ai.gemini_client import GeminiResponse
from zuhura.ai.tools import dispatch_tool_call


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["geodetic_datum"]["semi_major_radius_m"] == 3396190.0


@pytest.mark.asyncio
async def test_catalog_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/catalog/datasets")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 4
        ids = [d["id"] for d in data["datasets"]]
        assert "zuhura-mola-megdr-128" in ids
        assert "zuhura-viking-mdim21" in ids


@pytest.mark.asyncio
async def test_spatial_elevation_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Query near Jezero Crater
        response = await client.get("/api/v1/spatial/elevation?lat=18.38&lon=77.58")
        assert response.status_code == 200
        data = response.json()
        assert "elevation_m" in data
        assert data["datum"] == "Mars Areoid (MOLA GMM-2B)"


@pytest.mark.asyncio
async def test_missions_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/missions")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 5
        names = [m["name"] for m in data["missions"]]
        assert any("Perseverance" in name for name in names)


@pytest.mark.asyncio
async def test_ai_query_with_map_context():
    """The /query path returns the Gemini answer with citations from the tools it called."""
    elevation_call = await dispatch_tool_call("get_elevation_at_point", {"latitude": 18.38, "longitude": 77.58})
    gemini_reply = GeminiResponse(text="Jezero Crater floor is about -2,600 m.", tool_calls=[elevation_call])

    with patch("zuhura.ai.scientist_engine.gemini_client.is_available", return_value=True), patch(
        "zuhura.ai.scientist_engine.MarsScientistEngine._chat_with_gemini", return_value=gemini_reply
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            payload = {
                "prompt": "What is the elevation at this crater?",
                "map_context": {
                    "camera_lat": 18.38,
                    "camera_lon": 77.58,
                    "camera_altitude_m": 25000.0,
                    "active_layers": ["zuhura-mola-megdr-128"],
                },
            }
            response = await client.post("/api/v1/ai/query", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert len(data["citations"]) > 0
            assert data["citations"][0]["dataset_id"] == "zuhura-mola-megdr-128"
            assert len(data["executed_tools"]) > 0
