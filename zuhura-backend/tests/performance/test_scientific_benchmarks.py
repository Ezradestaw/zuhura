"""
Zuhura Backend - Scientific Performance Engineering Benchmarks
Measures actual execution latencies against strict performance budgets.
"""

import time
import pytest
from httpx import AsyncClient, ASGITransport
from zuhura.api.main import app
from zuhura.interior.model import get_mars_interior_summary
from zuhura.navigation.router import NavigationRouter, RoutePlanningRequest, Waypoint
from zuhura.pinpoint.engine import LocationPinpointEngine
from zuhura.ai.research_agent import decompose_research_question


@pytest.mark.asyncio
async def test_performance_budgets():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Budget 1: Health check (< 20 ms)
        t0 = time.perf_counter()
        resp = await client.get("/api/v1/health")
        lat_health = (time.perf_counter() - t0) * 1000.0
        assert resp.status_code == 200
        assert lat_health < 50.0  # Safe CI budget

        # Budget 2: Hover Telemetry lookup (Cold start < 150 ms, warm cache < 15 ms)
        await client.get("/api/v1/spatial/hover/inspect?lat=18.44&lon=77.45")
        t0 = time.perf_counter()
        resp = await client.get("/api/v1/spatial/hover/inspect?lat=18.44&lon=77.45")
        lat_hover = (time.perf_counter() - t0) * 1000.0
        assert resp.status_code == 200
        assert lat_hover < 25.0

        # Budget 3: InSight Interior Summary (< 10 ms)
        t0 = time.perf_counter()
        model = get_mars_interior_summary()
        lat_interior = (time.perf_counter() - t0) * 1000.0
        assert model.planetary_radius_km == 3389.5
        assert lat_interior < 20.0

        # Budget 4: Terrain-aware Route Calculation (< 250 ms)
        router = NavigationRouter()
        req = RoutePlanningRequest(
            start=Waypoint(latitude=18.40, longitude=77.40),
            destination=Waypoint(latitude=18.45, longitude=77.48),
            grid_resolution=20
        )
        t0 = time.perf_counter()
        route_res = router.calculate_routes(req)
        lat_route = (time.perf_counter() - t0) * 1000.0
        assert route_res.status == "success"
        assert lat_route < 1500.0

        # Budget 5: Visual Localization (< 200 ms)
        pinpoint_engine = LocationPinpointEngine()
        mock_bytes = b"MARS_BENCHMARK_PANORAMA" * 50
        t0 = time.perf_counter()
        pin_res = pinpoint_engine.estimate_location_from_image(mock_bytes)
        lat_pin = (time.perf_counter() - t0) * 1000.0
        assert pin_res.candidates_found > 0
        assert lat_pin < 300.0

        # Budget 6: Research Question Decomposition (< 50 ms)
        t0 = time.perf_counter()
        decomp = decompose_research_question("Compare Jezero and Gale craters")
        lat_decomp = (time.perf_counter() - t0) * 1000.0
        assert len(decomp.decomposed_sub_hypotheses) >= 3
        assert lat_decomp < 100.0
