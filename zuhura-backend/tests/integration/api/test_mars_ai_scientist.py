"""
Tests for the assistant API, Gemini client and data tools.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock

from zuhura.api.main import app
from zuhura.ai.tools import dispatch_tool_call, SCIENTIFIC_TOOLS_REGISTRY
from zuhura.ai.grounding import GroundingManager
from zuhura.ai.gemini_client import GeminiClient, GeminiResponse, GeminiUsage


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _gemini_answer(text: str = "Jezero Crater lies at about -2,600 m.") -> GeminiResponse:
    return GeminiResponse(
        text=text,
        tool_calls=[],
        usage=GeminiUsage(prompt_tokens=10, candidate_tokens=8, total_tokens=18),
        model="gemini-3.5-flash-lite",
    )


@pytest.mark.anyio
async def test_ai_health_endpoint():
    """Health reports the tool registry and whether Gemini is configured."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/ai/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "assistant"
        assert data["status"] in ("healthy", "unavailable")
        assert data["provider"]["name"] == "gemini"
        assert data["scientific_registry"]["registered_tools_count"] >= 10
        assert "get_elevation_at_point" in data["scientific_registry"]["tools"]


@pytest.mark.anyio
async def test_ai_models_endpoint():
    """Models reports the configured Gemini model, or null without a key."""
    with patch("zuhura.api.v1.ai.gemini_client.is_available", return_value=False):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/ai/models")
            assert response.status_code == 200
            assert response.json() == {"current_active_model": None, "available": False}


@pytest.mark.anyio
async def test_ai_chat_unavailable_without_key():
    """Without a Gemini key the chat endpoint returns 503 and an explanation, not a scripted answer."""
    with patch("zuhura.ai.scientist_engine.gemini_client.is_available", return_value=False):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/ai/chat", json={"prompt": "What is the elevation here?"})
            assert response.status_code == 503
            assert "GEMINI_API_KEY" in response.json()["detail"]


@pytest.mark.anyio
async def test_ai_chat_unavailable_when_gemini_fails():
    """A Gemini error is reported as 503."""
    with patch("zuhura.ai.scientist_engine.gemini_client.is_available", return_value=True), patch(
        "zuhura.ai.scientist_engine.MarsScientistEngine._chat_with_gemini", side_effect=RuntimeError("boom")
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/ai/chat", json={"prompt": "Hello"})
            assert response.status_code == 503


@pytest.mark.anyio
async def test_ai_chat_returns_gemini_answer():
    """A successful Gemini answer is returned with its provider and map context."""
    with patch("zuhura.ai.scientist_engine.gemini_client.is_available", return_value=True), patch(
        "zuhura.ai.scientist_engine.MarsScientistEngine._chat_with_gemini", return_value=_gemini_answer()
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ai/chat",
                json={"prompt": "Elevation of Jezero?", "map_context": {"camera_lat": 18.38, "camera_lon": 77.58}},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["provider"] == "gemini"
            assert "Jezero" in data["answer"]
            assert data["context_applied"]["latitude"] == 18.38


@pytest.mark.anyio
async def test_ai_chat_stream_unavailable_without_key():
    """The stream sends an error event when the assistant is not configured."""
    with patch("zuhura.ai.scientist_engine.gemini_client.is_available", return_value=False):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/ai/chat/stream", json={"prompt": "Slope here?"})
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]
            assert "event: error" in response.text
            assert "event: chunk" not in response.text


@pytest.mark.anyio
async def test_ai_location_analysis():
    """Test instant coordinate multi-sensor analysis endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "latitude": 18.65,
            "longitude": 226.2,
            "altitude_m": 50000.0
        }
        response = await client.post("/api/v1/ai/analyze-location", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["coordinate"]["latitude"] == 18.65
        assert data["elevation"]["elevation_m"] == 20020.0
        assert data["elevation"]["nearby_named_feature"]["name"] == "Olympus Mons"
        assert "slope_deg" in data["morphometry"]["derivatives"]
        assert data["solar_illumination"]["solar_elevation_deg"] is not None


@pytest.mark.anyio
async def test_ai_region_analysis():
    """Test regional bounding box planetary analysis endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "min_lat": 18.0,
            "max_lat": 19.0,
            "min_lon": 77.0,
            "max_lon": 78.0
        }
        response = await client.post("/api/v1/ai/analyze-region", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "regional_statistics" in data
        assert "catalog_coverage" in data


@pytest.mark.anyio
async def test_ai_conversation_lifecycle():
    """Test creating, fetching, and deleting research conversation sessions."""
    with patch("zuhura.ai.scientist_engine.gemini_client.is_available", return_value=True), patch(
        "zuhura.ai.scientist_engine.MarsScientistEngine._chat_with_gemini", return_value=_gemini_answer()
    ):
        await _run_conversation_lifecycle()


async def _run_conversation_lifecycle():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        session_id = "pytest-lifecycle-session"
        # 1. Send chat turn
        res1 = await client.post("/api/v1/ai/chat", json={
            "prompt": "What missions landed near Jezero?",
            "session_id": session_id,
            "map_context": {"camera_lat": 18.38, "camera_lon": 77.58}
        })
        assert res1.status_code == 200

        # 2. Get conversation
        res2 = await client.get(f"/api/v1/ai/conversations/{session_id}")
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["session_id"] == session_id
        assert len(data2["history"]) >= 2

        # 3. List conversations
        res3 = await client.get("/api/v1/ai/conversations")
        assert res3.status_code == 200
        sids = [c["session_id"] for c in res3.json()["conversations"]]
        assert session_id in sids

        # 4. Delete conversation
        res4 = await client.delete(f"/api/v1/ai/conversations/{session_id}")
        assert res4.status_code == 200
        assert res4.json()["status"] == "deleted"

        # 5. Fetch after deletion -> 404
        res5 = await client.get(f"/api/v1/ai/conversations/{session_id}")
        assert res5.status_code == 404


@pytest.mark.anyio
async def test_tool_argument_validation():
    """Verify tool parameter validation rejects invalid coordinates or kernel sizes."""
    # Invalid latitude > 90
    res_lat = await dispatch_tool_call("get_elevation_at_point", {"latitude": 105.0, "longitude": 77.0})
    assert res_lat["status"] == "error"
    assert "Input should be less than or equal to 90" in res_lat["error"]

    # Invalid kernel size (4 instead of 3, 5, or 7)
    res_kernel = await dispatch_tool_call("get_terrain_morphometry", {"latitude": 18.0, "longitude": 77.0, "kernel_size": 4})
    assert res_kernel["status"] == "error"
    assert "Kernel size must be 3, 5, or 7" in res_kernel["error"]


@pytest.mark.anyio
async def test_gemini_client_fallback_on_unconfigured_or_quota():
    """Verify GeminiClient detects missing key or quota exhaustion and triggers fallback."""
    # Test client without key
    client_empty = GeminiClient(api_key="")
    assert not client_empty.is_available()
    resp_empty = await client_empty.generate("Test prompt")
    assert resp_empty.is_fallback is True

    # Test client with simulated quota exhaustion (HTTP 429)
    client_quota = GeminiClient(api_key="AIzaSyDummyKeyForTestingQuotaDetection")
    with patch.object(client_quota, "_client", MagicMock()) as mock_client:
        mock_models = MagicMock()
        mock_client.models = mock_models
        from google.genai.errors import APIError
        # Simulate APIError 429
        err = APIError(429, {"error": {"message": "RESOURCE_EXHAUSTED: Quota exceeded for quota group", "code": 429}})
        mock_models.generate_content.side_effect = err

        resp_quota = await client_quota.generate("Test prompt")
        assert resp_quota.is_fallback is True
        assert resp_quota.quota_exhausted is True


@pytest.mark.anyio
async def test_dispatch_new_advanced_tools():
    """Verify dispatch_tool_call executes new advanced planetary science tools."""
    # 2. Optimize route
    res_nav = await dispatch_tool_call("optimize_navigation_route", {
        "start_latitude": 18.38,
        "start_longitude": 77.58,
        "end_latitude": 18.44,
        "end_longitude": 77.45,
        "mobility_profile": "rover_perseverance",
        "preference": "minimum_slope"
    })
    assert res_nav["status"] == "completed"
    assert "recommended_route" in res_nav["result"]

    # 3. Hover inspect
    res_hov = await dispatch_tool_call("inspect_hover_location", {"latitude": 18.38, "longitude": 77.58})
    assert res_hov["status"] == "completed"
    assert res_hov["result"]["geological_era"] is not None

    # 4. Pinpoint image matching
    res_pin = await dispatch_tool_call("pinpoint_mars_landscape_image", {"mission_hint": "Perseverance"})
    assert res_pin["status"] == "completed"
    assert res_pin["result"]["candidates_found"] > 0

    # 5. Region discovery
    res_reg = await dispatch_tool_call("discover_geological_regions", {
        "center_latitude": 18.38,
        "center_longitude": 77.58,
        "search_radius_km": 50.0
    })
    assert res_reg["status"] == "completed"
    assert res_reg["result"]["total_regions_discovered"] >= 2

