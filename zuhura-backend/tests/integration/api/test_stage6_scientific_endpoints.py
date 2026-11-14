"""
Zuhura Backend - Stage 6 Scientific Endpoints Integration Tests
Tests:
  1. GET /api/v1/elevation (valid point, Olympus Mons, NoData boundary, longitude wrapping)
  2. GET /api/v1/catalog/search (filters, bounding box, pagination)
  3. GET /api/v1/catalog/products/{product_id} (valid product, 404 handling)
  4. GET /api/v1/rasters/{product_id}/metadata (GDAL dimensions, overviews, bands)
  5. GET /api/v1/rasters/{product_id} (secure access, path traversal prevention)
  6. GET /api/v1/tiles/cog/{z}/{x}/{y}.png (dynamic COG tile rendering, PNG format, cache headers)
"""

import pytest
from httpx import ASGITransport, AsyncClient
from zuhura.api.main import app


@pytest.mark.asyncio
async def test_elevation_endpoint_valid_point():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Query Jezero Crater floor (18.38 N, 77.58 E)
        resp = await client.get("/api/v1/elevation?latitude=18.38&longitude=77.58")
        assert resp.status_code == 200
        data = resp.json()
        assert data["latitude"] == 18.38
        assert data["longitude"] == 77.58
        assert -2800 <= data["elevation_m"] <= -2400  # Jezero Crater is approx -2.6 km
        assert data["nodata_status"] is False
        assert data["dataset_id"] == "zuhura-mola-global-v3-cog"
        assert data["vertical_reference"] == "MOLA GMM-3 Areoid (Equipotential Reference Surface)"
        assert data["validation_status"] == "scientifically_validated"


@pytest.mark.asyncio
async def test_elevation_endpoint_olympus_mons():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Query Olympus Mons Caldera (18.65 N, 226.2 E)
        resp = await client.get("/api/v1/elevation?lat=18.65&lon=226.2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["elevation_m"] > 19000  # Over 19 km elevation
        assert data["nodata_status"] is False


@pytest.mark.asyncio
async def test_elevation_endpoint_longitude_wrapping():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Query with negative longitude (-282.42 == 77.58 East)
        resp = await client.get("/api/v1/elevation?lat=18.38&lon=-282.42")
        assert resp.status_code == 200
        data = resp.json()
        assert -2800 <= data["elevation_m"] <= -2400
        assert round(data["longitude"], 2) == 77.58


@pytest.mark.asyncio
async def test_elevation_endpoint_out_of_bounds_nodata():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Latitude outside global MEG128 boundary (> 88 degrees)
        resp = await client.get("/api/v1/elevation?latitude=89.2&longitude=45.0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["elevation_m"] is None
        assert data["nodata_status"] is True
        assert data["validation_status"] == "outside_coverage_boundary"


@pytest.mark.asyncio
async def test_elevation_missing_params():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/elevation")
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_catalog_search_filters_and_pagination():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Search by instrument
        resp_thm = await client.get("/api/v1/catalog/search?instrument=THEMIS")
        assert resp_thm.status_code == 200
        d_thm = resp_thm.json()
        assert d_thm["total"] >= 10
        assert all("THEMIS" in item["instrument"] for item in d_thm["items"])

        # 2. Search by Bounding Box over Jezero Crater (76.5,18.0,78.5,19.0)
        resp_bbox = await client.get("/api/v1/catalog/search?bbox=76.5,18.0,78.5,19.0&page=1&page_size=5")
        assert resp_bbox.status_code == 200
        d_bbox = resp_bbox.json()
        assert d_bbox["total"] >= 5
        assert len(d_bbox["items"]) <= 5
        assert d_bbox["page"] == 1
        assert d_bbox["page_size"] == 5
        assert d_bbox["total_pages"] >= 1

        # 3. Invalid bbox format
        resp_bad_bbox = await client.get("/api/v1/catalog/search?bbox=invalid,bbox")
        assert resp_bad_bbox.status_code == 400


@pytest.mark.asyncio
async def test_catalog_product_detail():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Known product ID
        resp = await client.get("/api/v1/catalog/products/mola_global_meg128_cog")
        assert resp.status_code == 200
        data = resp.json()
        assert data["dataset_id"] == "zuhura-mola-global-v3-cog"
        assert data["instrument"] == "MOLA"
        assert data["resolution"] == 463.0577

        # Unknown product ID
        resp_404 = await client.get("/api/v1/catalog/products/non_existent_product_123")
        assert resp_404.status_code == 404


@pytest.mark.asyncio
async def test_raster_metadata_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/rasters/mola_global_meg128_cog/metadata")
        assert resp.status_code == 200
        data = resp.json()
        assert data["dimensions"] == [46080, 22528, 1]
        assert data["overview_count"] == 7
        assert data["data_type"] == "Int16"
        assert "Mars_simpCyl_c180" in data["projection_wkt"]


@pytest.mark.asyncio
async def test_raster_security_path_traversal():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Attempt to access non-cataloged path or traversal
        resp = await client.get("/api/v1/rasters/../../etc/passwd")
        assert resp.status_code in [404, 403]


@pytest.mark.asyncio
async def test_dynamic_cog_tile_rendering():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Request tile at zoom 2, x=2, y=1
        resp = await client.get("/api/v1/tiles/cog/2/2/1.png?colormap=terrain")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        assert len(resp.content) > 100
        assert resp.content[:8] == b"\x89PNG\r\n\x1a\n"

@pytest.mark.asyncio
async def test_terrain_quantized_mesh_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Test layer.json metadata
        resp_layer = await client.get("/api/v1/tiles/terrain/jezero/layer.json")
        assert resp_layer.status_code == 200
        d_layer = resp_layer.json()
        assert d_layer["format"] == "quantized-mesh-1.0"
        assert d_layer["scheme"] == "tms"
        assert d_layer["bounds"] == [76.5, 18.0, 78.5, 19.0]

        # 2. Test binary terrain tile (level 9, x=732, y=203)
        resp_tile = await client.get("/api/v1/tiles/terrain/jezero/9/732/203.terrain")
        assert resp_tile.status_code == 200
        assert "quantized-mesh" in resp_tile.headers["content-type"]
        assert len(resp_tile.content) >= 88  # Header size minimum
