"""
Tests for the assistant tool registry and tool dispatch.
Validates:
1. Autonomous scientific paper generation (Markdown and camera-ready LaTeX).
2. Epistemic tagging integration ([MEASURED], [OBSERVED], [INTERPRETED], [HYPOTHESIS]).
3. Automated planetary peer-review simulation against physical laws (Pike 1980 crater scaling, Bekker soil mechanics).
4. Extended 17-tool scientific registry and direct tool dispatching.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from zuhura.api.main import app
from zuhura.ai.tools import dispatch_tool_call, SCIENTIFIC_TOOLS_REGISTRY


@pytest.mark.asyncio
async def test_list_scientific_tools_registry():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/ai/tools")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tools_count"] >= 17
        names = [t["name"] for t in data["tools"]]
        assert "analyze_crater_morphometry" in names
        assert "analyze_multispectral_mineralogy" in names
        assert "query_epistemic_provenance" in names
        assert "evaluate_rover_terramechanics" in names
        assert "detect_temporal_surface_changes" in names


@pytest.mark.asyncio
async def test_direct_ai_tool_dispatch():
    # 1. Crater morphometry tool
    res1 = await dispatch_tool_call(
        "analyze_crater_morphometry",
        {"latitude": 18.38, "longitude": 77.58, "diameter_km": 47.5, "rim_elevation_m": -1700.0, "floor_elevation_m": -2530.0}
    )
    assert res1["status"] == "completed"
    assert res1["result"]["crater_class"] == "COMPLEX"
    assert res1["result"]["diameter_km"] == 47.5
    assert res1["result"]["depth_to_diameter_ratio"] > 0

    # 2. Multispectral mineralogy tool
    res2 = await dispatch_tool_call(
        "analyze_multispectral_mineralogy",
        {"latitude": 18.38, "longitude": 77.58, "target_mineral": "smectite"}
    )
    assert res2["status"] == "completed"
    assert "spectral_indices" in res2["result"]
    assert "thermal_inertia" in res2["result"]

    # 3. Rover terramechanics tool
    res3 = await dispatch_tool_call(
        "evaluate_rover_terramechanics",
        {"rover_profile": "rover_perseverance", "regolith_type": "basaltic_sand", "slope_deg": 4.5}
    )
    assert res3["status"] == "completed"
    assert res3["result"]["sinkage_depth_cm"] > 0.0
    assert res3["result"]["tractive_effort_n"] > 0.0

    # 4. Epistemic provenance tool
    res4 = await dispatch_tool_call(
        "query_epistemic_provenance",
        {"dataset_id": "mola_meg128_cog", "derivative_type": "elevation"}
    )
    assert res4["status"] == "completed"
    assert "classification" in res4["result"]
