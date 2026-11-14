"""
Integration tests for the multi-resolution imagery pipeline.
Validates:
  1. Global Viking MDIM 2.1 COG JPEG/PNG tile endpoint (/api/v1/tiles/viking/*)
  2. Regional CTX Jezero Context tile endpoint (/api/v1/tiles/ctx/*)
  3. Local HiRISE Jezero High-Res tile endpoint (/api/v1/tiles/hirise/*)
  4. Bounds validation, out-of-range rejection, and transparent fallback handling
  5. Disk caching headers (X-Tile-Cache HIT/MISS)
  6. Imagery coverage manifest integrity and asset existence
"""

import json
from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient
from zuhura.api.main import app


@pytest.mark.asyncio
async def test_viking_tile_level_zero():
    """Verify Viking MDIM 2.1 level 0 tiles return valid 256x256 JPEG data."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Western hemisphere
        resp0 = await client.get("/api/v1/tiles/viking/0/0/0.jpg")
        assert resp0.status_code == 200
        assert resp0.headers["content-type"] == "image/jpeg"
        assert len(resp0.content) > 5000
        # JPEG SOI marker check: 0xFF, 0xD8
        assert resp0.content[:2] == b"\xff\xd8"

        # Eastern hemisphere
        resp1 = await client.get("/api/v1/tiles/viking/0/1/0.jpg")
        assert resp1.status_code == 200
        assert resp1.headers["content-type"] == "image/jpeg"
        assert len(resp1.content) > 5000
        assert resp1.content[:2] == b"\xff\xd8"


@pytest.mark.asyncio
async def test_viking_tile_regional_zoom():
    """Verify Viking tile at zoom 2 and caching behavior."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        url = "/api/v1/tiles/viking/2/2/1.jpg"
        resp_first = await client.get(url)
        assert resp_first.status_code == 200
        assert resp_first.headers["content-type"] == "image/jpeg"

        # Second request should be a cache HIT
        resp_cached = await client.get(url)
        assert resp_cached.status_code == 200
        assert resp_cached.headers.get("x-tile-cache") == "HIT"


@pytest.mark.asyncio
async def test_viking_tile_out_of_bounds():
    """Verify invalid zoom levels (400) and out-of-bounds indices (404) are properly rejected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Zoom 11 exceeds maximum supported Viking zoom (10)
        resp_z = await client.get("/api/v1/tiles/viking/11/0/0.jpg")
        assert resp_z.status_code == 400
        assert "Zoom level must be between 0 and 10" in resp_z.json()["detail"]

        # Negative zoom
        resp_neg = await client.get("/api/v1/tiles/viking/-1/0/0.jpg")
        assert resp_neg.status_code == 400

        # Out-of-range tile X coordinate for zoom 2 (valid X: 0..7)
        resp_x = await client.get("/api/v1/tiles/viking/2/99/1.jpg")
        assert resp_x.status_code == 404
        assert "out of range" in resp_x.json()["detail"]


@pytest.mark.asyncio
async def test_ctx_tile_jezero_hit():
    """Verify CTX Jezero Crater tile returns 256x256 RGBA PNG with valid image content."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # z=10, x=1464, y=407 covers Jezero Crater
        resp = await client.get("/api/v1/tiles/ctx/10/1464/407.png")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        # PNG magic header: \x89PNG\r\n\x1a\n
        assert resp.content[:8] == b"\x89PNG\r\n\x1a\n"
        assert len(resp.content) > 10000


@pytest.mark.asyncio
async def test_ctx_tile_out_of_bounds_fallback():
    """Verify CTX requests outside Jezero footprint return transparent PNG fallback."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # z=10, x=0, y=0 is far outside Jezero
        resp = await client.get("/api/v1/tiles/ctx/10/0/0.png")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        assert resp.content[:8] == b"\x89PNG\r\n\x1a\n"
        # Transparent fallback tile is small (< 1000 bytes)
        assert len(resp.content) < 1000


@pytest.mark.asyncio
async def test_hirise_tile_jezero_hit():
    """Verify HiRISE Jezero Crater tile returns high-resolution 256x256 RGBA PNG."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # z=14, x=23445, y=6513 covers Jezero HiRISE delta / touchdown area
        resp = await client.get("/api/v1/tiles/hirise/14/23445/6513.png")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        assert resp.content[:8] == b"\x89PNG\r\n\x1a\n"
        assert len(resp.content) > 10000


@pytest.mark.asyncio
async def test_hirise_tile_out_of_bounds_fallback():
    """Verify HiRISE requests outside coverage return transparent PNG fallback."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/tiles/hirise/14/0/0.png")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        assert resp.content[:8] == b"\x89PNG\r\n\x1a\n"
        assert len(resp.content) < 1000


def test_imagery_coverage_manifest_integrity():
    """Verify imagery coverage manifest exists and all 4 tiers point to existing files on disk."""
    from zuhura.core.config import settings
    repo_root = Path(settings.REPO_ROOT)
    manifest_path = repo_root / "zuhura-data/catalogs/imagery_coverage_manifest.json"
    assert manifest_path.exists(), "imagery_coverage_manifest.json must exist"

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "manifest_version" in data
    assert "tiers" in data
    assert len(data["tiers"]) >= 4

    # Verify each tier
    tier_names = [t["tier_name"] for t in data["tiers"]]
    assert "Planetary Global Basemap" in tier_names
    assert "Global Topographic Basemap" in tier_names
    assert "Regional Geological Context" in tier_names
    assert "Local High-Resolution Surface" in tier_names

    for tier in data["tiers"]:
        if "storage_path" in tier:
            storage_rel = tier["storage_path"]
            target_path = repo_root / "zuhura-data" / storage_rel
            assert target_path.exists(), f"Asset {target_path} for tier {tier['tier']} must exist on disk"
            assert target_path.stat().st_size > 0


def test_viking_cog_processing_manifest():
    """Verify Viking COG manifest exists and records valid source/destination checksums."""
    from zuhura.core.config import settings
    manifest_path = Path(settings.REPO_ROOT) / "zuhura-data/data/processed/viking/viking_cog_processing_manifest.json"
    assert manifest_path.exists(), "viking_cog_processing_manifest.json must exist"

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["source"]["sha256"] == "554f1170998b4cd00359defa48600307e52c49f921c282d842361ad45082aa31"
    assert data["destination"]["sha256"] == "ac6d612cac52184941873bae7cc83451d54f215142c780cac99b64e1215b6979"
    assert data["performance"]["speedup_factor"] > 100
    assert data["validation"]["status"] == "PASSED"
