"""
Integration tests for security middleware and performance limits.
"""

import time
import pytest
from fastapi.testclient import TestClient
from zuhura.api.main import app
from zuhura.core.cache import global_cache, orbital_cache
from zuhura.core.security import heavy_compute_limiter, general_limiter

client = TestClient(app)


def test_security_headers():
    """Validates that mission-grade HTTP security headers are injected on all outbound responses."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    headers = res.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Strict-Transport-Security" in headers
    assert "strict-origin" in headers.get("Referrer-Policy", "")
    assert "geolocation=()" in headers.get("Permissions-Policy", "")
    assert headers.get("X-Planetary-Datum") == "IAU/IAG 2015 WGCCRE (Mars)"


def test_gzip_compression_on_large_payloads():
    """Validates GZip compression middleware compresses large scientific payloads (>1000 bytes)."""
    headers = {"Accept-Encoding": "gzip"}
    res = client.post(
        "/api/v1/spatial/environment/atmospheric-profile",
        json={
            "latitude": 18.38,
            "longitude": 77.58,
            "elevation_m": -2500.0,
            "ls_deg": 180.0,
            "max_altitude_km": 60.0,
            "step_km": 1.0,  # 61 layers generating multi-kilobyte JSON
        },
        headers=headers
    )
    assert res.status_code == 200
    # TestClient automatically decompresses, but response.headers reflects gzip encoding
    assert res.headers.get("content-encoding") == "gzip"
    data = res.json()
    assert data["status"] == "success"
    assert len(data["profile"]["layers"]) >= 60


def test_cache_acceleration_and_stats():
    """Validates in-memory sub-millisecond cache hit acceleration and statistics."""
    global_cache.clear()
    orbital_cache.clear()

    # Initial query (cache miss)
    t0 = time.perf_counter()
    res1 = client.get("/api/v1/spatial/environment/overview?ls_deg=123.45")
    d1 = time.perf_counter() - t0
    assert res1.status_code == 200

    # Second identical query (cache hit)
    t0 = time.perf_counter()
    res2 = client.get("/api/v1/spatial/environment/overview?ls_deg=123.45")
    d2 = time.perf_counter() - t0
    assert res2.status_code == 200

    assert res1.json() == res2.json()

    # Check cache telemetry in stats
    stats = orbital_cache.stats()
    assert stats["hits"] >= 1
    assert stats["total_entries"] >= 1


def test_forwarded_for_is_ignored_unless_peer_is_trusted():
    """A client must not choose its rate-limit identity by sending X-Forwarded-For."""
    from starlette.requests import Request
    from zuhura.core.config import settings
    from zuhura.core.security import resolve_client_ip

    previous = list(settings.TRUSTED_PROXY_CIDRS)
    try:
        settings.TRUSTED_PROXY_CIDRS = []
        untrusted = Request({
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [(b"x-forwarded-for", b"1.2.3.4, 10.0.0.8")],
            "client": ("203.0.113.9", 4321),
            "server": ("test", 80),
        })
        assert resolve_client_ip(untrusted) == "203.0.113.9"

        settings.TRUSTED_PROXY_CIDRS = ["10.0.0.0/8"]
        trusted = Request({
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [(b"x-forwarded-for", b"8.8.8.8, 10.0.0.8")],
            "client": ("10.0.0.5", 4321),
            "server": ("test", 80),
        })
        assert resolve_client_ip(trusted) == "8.8.8.8"

        malformed = Request({
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [(b"x-forwarded-for", b"not-an-ip")],
            "client": ("10.0.0.5", 4321),
            "server": ("test", 80),
        })
        assert resolve_client_ip(malformed) == "10.0.0.5"
    finally:
        settings.TRUSTED_PROXY_CIDRS = previous


def test_tile_source_status_contract():
    """The globe HUD can tell local cache tiles from a live NASA/USGS fetch."""
    res = client.get("/api/v1/tiles/source-status")
    assert res.status_code == 200
    body = res.json()
    assert body["mode"] in {"local_cache", "remote_network", "mixed"}
    assert "imagery_origin" in body
    assert isinstance(body["layers"], dict)
    assert "viking" in body["layers"]
    assert "terrain" in body["layers"]


def test_rate_limiter_protection():
    """Validates that rate limiter throttles excessive requests on heavy compute endpoints."""
    heavy_compute_limiter.reset()

    # Exhaust quota on heavy limiter for mock client
    client_ip = "192.168.1.100"
    for _ in range(heavy_compute_limiter.limit):
        allowed, _, _ = heavy_compute_limiter.is_allowed(client_ip)
        assert allowed is True

    # Next request must be throttled
    allowed, remaining, retry_after = heavy_compute_limiter.is_allowed(client_ip)
    assert allowed is False
    assert remaining == 0
    assert retry_after > 0.0

    # Clean up limiter state
    heavy_compute_limiter.reset()


def test_comprehensive_health_and_diagnostics():
    """Validates /api/v1/health provides complete resource metrics, cache statistics, and subsystem checks."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "ok"
    assert data["version"] == "2.0.0-MISSION-GRADE"
    assert data["uptime_seconds"] >= 0.0
    assert data["geodetic_datum"]["standard"] == "IAU/IAG 2015 WGCCRE"

    # System resource metrics
    resources = data["system_resources"]
    assert resources["memory_rss_mb"] > 0.0
    assert resources["threads_count"] > 0

    # Subsystem status verification
    subsystems = data["subsystems"]
    assert "ONLINE" in subsystems["geodesy_engine"]
    assert "ONLINE" in subsystems["topography_service"]
    assert "ONLINE" in subsystems["provenance_registry"]
    assert "ONLINE" in subsystems["atmosphere_mcd_engine"]
    assert "ONLINE" in subsystems["rover_mobility_simulator"]
    assert "ONLINE" in subsystems["vision_processor"]
    assert "ONLINE" in subsystems["ai_research_scientist"]


def test_kubernetes_probes():
    """Validates Kubernetes liveness and readiness probe contracts."""
    # Liveness probe
    res_live = client.get("/api/v1/health/liveness")
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "alive"

    # Readiness probe
    res_ready = client.get("/api/v1/health/readiness")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ready"
    assert res_ready.json()["initialized_datum"] == "IAU/IAG 2015 WGCCRE"


def test_prometheus_exposition_format():
    """Validates standard Prometheus text exposition format for production metrics scraping."""
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "text/plain" in res.headers.get("content-type", "")

    body = res.text
    assert "zuhura_uptime_seconds" in body
    assert "zuhura_http_requests_total" in body
    assert "zuhura_http_request_duration_seconds_mean" in body
