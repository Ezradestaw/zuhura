"""
Zuhura Planetary Digital Twin - Stage 5 Automated Test Suite
Tests:
  1. Unified Scientific Data Models (Pydantic validation, conventions)
  2. Provenance state machine (enforcing allowed transitions, rejecting skips)
  3. Spatial geometry, polygon intersections, and longitude wrapping around 0°/360°
  4. Catalog building, persistence, and multi-criteria searching
  5. Cross-instrument spatial overlap calculations (Jezero pilot)
  6. Coordinate elevation queries directly from MOLA COG
  7. Data access client interfaces
"""

from datetime import datetime, timezone
from pathlib import Path
import pytest

from zuhura_data.models.spatial import (
    BoundingBox,
    CoordinateConvention,
    LongitudeConvention,
    SpatialCoverage,
    normalize_longitude_180,
    normalize_longitude_360
)
from zuhura_data.models.provenance import (
    FileProvenance,
    ProcessingStep,
    ProvenanceHistory,
    ValidationStatus
)
from zuhura_data.models.scientific_product import (
    CalibrationInfo,
    DatasetFamily,
    NoDataPolicy,
    ProductLevel,
    ProductType,
    ScientificProduct
)
from zuhura_data.models.catalog import GeodeticFramework, ScientificCatalog
from zuhura_data.catalog.builder import build_unified_catalog
from zuhura_data.catalog.manager import CatalogManager
from zuhura_data.spatial.alignment import (
    calculate_polygon_overlap,
    deg2_to_km2_at_latitude
)
from zuhura_data.access.client import ZuhuraScienceAccess

REPO_ROOT = Path(__file__).resolve().parent.parent


# =============================================================================
# 1. Spatial Coordinates & Longitude Wrapping Tests
# =============================================================================

def test_longitude_normalization():
    """Verify longitude wrapping into [0, 360) and [-180, 180)."""
    assert normalize_longitude_360(0.0) == 0.0
    assert normalize_longitude_360(360.0) == 0.0
    assert normalize_longitude_360(-10.0) == 350.0
    assert normalize_longitude_360(720.0) == 0.0

    assert normalize_longitude_180(0.0) == 0.0
    assert normalize_longitude_180(350.0) == -10.0
    assert normalize_longitude_180(180.0) == 180.0
    assert normalize_longitude_180(-10.0) == -10.0


def test_bounding_box_validation():
    """Verify latitude validation and prime meridian wrapping detection."""
    # Valid normal box
    b = BoundingBox(min_lon=76.5, max_lon=78.5, min_lat=18.0, max_lat=19.0)
    assert not b.crosses_prime_meridian
    assert b.contains_point(18.5, 77.0)
    assert not b.contains_point(20.0, 77.0)

    # Inverted latitude should fail validation
    with pytest.raises(ValueError):
        BoundingBox(min_lon=10.0, max_lon=20.0, min_lat=30.0, max_lat=10.0)

    # Box crossing prime meridian (e.g. 350° to 10° East)
    wrap_box = BoundingBox(min_lon=350.0, max_lon=10.0, min_lat=-5.0, max_lat=5.0)
    assert wrap_box.crosses_prime_meridian
    assert wrap_box.contains_point(0.0, 355.0)
    assert wrap_box.contains_point(0.0, 5.0)
    assert not wrap_box.contains_point(0.0, 180.0)
    assert "MULTIPOLYGON" in wrap_box.to_wkt()


# =============================================================================
# 2. Provenance State Machine & Transition Tests
# =============================================================================

def test_provenance_valid_transitions():
    """Verify valid step-by-step progress through the provenance lifecycle."""
    prov = ProvenanceHistory(current_status=ValidationStatus.DISCOVERED)
    assert prov.current_status == ValidationStatus.DISCOVERED

    prov.transition_to(ValidationStatus.DOWNLOADED, "File downloaded via curl")
    assert prov.current_status == ValidationStatus.DOWNLOADED

    prov.transition_to(ValidationStatus.CHECKSUM_VERIFIED, "SHA-256 confirmed")
    assert prov.current_status == ValidationStatus.CHECKSUM_VERIFIED

    prov.transition_to(ValidationStatus.METADATA_VALIDATED, "PDS3 headers parsed")
    assert prov.current_status == ValidationStatus.METADATA_VALIDATED

    prov.transition_to(ValidationStatus.SCIENTIFICALLY_VALIDATED, "Physical units checked")
    assert prov.current_status == ValidationStatus.SCIENTIFICALLY_VALIDATED
    assert len(prov.status_log) == 4


def test_provenance_invalid_transitions():
    """Verify skipping mandatory verification steps is rejected."""
    prov = ProvenanceHistory(current_status=ValidationStatus.DOWNLOADED)

    # Skipping checksum_verified directly to scientifically_validated
    with pytest.raises(ValueError) as exc:
        prov.transition_to(ValidationStatus.SCIENTIFICALLY_VALIDATED, "Illegal skip")
    assert "Invalid state transition" in str(exc.value)

    # Jumping backwards to discovered from downloaded
    with pytest.raises(ValueError):
        prov.transition_to(ValidationStatus.DISCOVERED, "Illegal rollback")


# =============================================================================
# 3. Scientific Catalog Builder & Search Tests
# =============================================================================

def test_unified_catalog_builder():
    """Verify building the catalog indices local and discovered assets."""
    cat = build_unified_catalog()
    assert cat.product_count >= 30

    # Verify MOLA COG is present and validated
    mola = cat.get_by_id("zuhura-mola-global-v3-cog")
    assert mola is not None
    assert mola.dataset_family == DatasetFamily.MOLA
    assert mola.resolution == 463.0577
    assert mola.validation_status == ValidationStatus.SCIENTIFICALLY_VALIDATED
    assert mola.nodata_policy.datum_zero_is_valid is True

    # Verify THEMIS pilot
    thm = cat.get_by_id("zuhura-themis-ir-jezero")
    assert thm is not None
    assert thm.dataset_family == DatasetFamily.THEMIS
    assert thm.spectral_information.band_count == 10
    assert thm.units == "W/(m^2*sr*um)"

    # Verify CTX pilot
    ctx = cat.get_by_id("zuhura-ctx-jezero")
    assert ctx is not None
    assert ctx.dataset_family == DatasetFamily.CTX
    assert ctx.resolution == 5.55

    # Verify HiRISE pilot
    hi = cat.get_by_id("zuhura-hirise-jezero")
    assert hi is not None
    assert hi.dataset_family == DatasetFamily.HIRISE
    assert hi.resolution == 0.25


def test_catalog_search_filters():
    """Test catalog search across family, resolution, location, and time."""
    cat = build_unified_catalog()
    mgr = CatalogManager(cat)

    # 1. Filter by family
    ctx_list = mgr.search(family=DatasetFamily.CTX)
    assert len(ctx_list) >= 10
    assert all(p.dataset_family == DatasetFamily.CTX for p in ctx_list)

    # 2. Filter by resolution (< 1.0 m/px -> HiRISE)
    high_res = mgr.search(max_resolution=1.0)
    assert len(high_res) > 0
    assert all(p.dataset_family == DatasetFamily.HIRISE for p in high_res)

    # 3. Filter by location (Point in Jezero crater: 18.38 N, 77.58 E)
    jezero_prods = mgr.search(point=(18.38, 77.58))
    assert len(jezero_prods) >= 3  # MOLA, THEMIS, CTX/HiRISE
    pids = [p.dataset_id for p in jezero_prods]
    assert "zuhura-mola-global-v3-cog" in pids

    # 4. Filter by bounding box
    bbox_results = mgr.search(bbox=BoundingBox(min_lon=76.5, max_lon=78.5, min_lat=18.0, max_lat=19.0))
    assert len(bbox_results) >= 5


# =============================================================================
# 4. Cross-Instrument Spatial Overlap Calculations
# =============================================================================

def test_spatial_overlap_calculation():
    """Test polygon intersection calculations on Mars ellipsoid."""
    themis_wkt = "POLYGON ((76.815 24.494, 78.507 12.485, 77.952 12.452, 76.207 24.458, 76.815 24.494))"
    ctx_wkt = "POLYGON ((77.53 18.654, 77.62 17.9408, 77.13 17.8814, 77.04 18.5946, 77.53 18.654))"

    overlap = calculate_polygon_overlap(themis_wkt, ctx_wkt, reference_lat_deg=18.5)
    assert overlap["intersects"] is True
    assert overlap["intersection_area_km2"] > 1000.0
    assert overlap["overlap_percent_of_g2"] > 90.0  # Over 90% of CTX frame is inside THEMIS swath


# =============================================================================
# 5. Scientific Data Access Client & MOLA Elevation Query Tests
# =============================================================================

def test_elevation_lookup_at_points():
    """Test fast single-pixel elevation queries on MOLA COG."""
    client = ZuhuraScienceAccess(repo_root=REPO_ROOT)

    # Jezero Crater floor (-2648 m)
    res_jezero = client.get_elevation_at_point(18.38, 77.58)
    assert res_jezero["nodata_status"] is False
    assert -2800 <= res_jezero["elevation_m"] <= -2400
    assert res_jezero["vertical_datum"] == "MOLA GMM-3 Areoid (Equipotential Reference Surface)"

    # Olympus Mons Caldera (+20,015 m)
    res_olympus = client.get_elevation_at_point(18.65, 226.2)
    assert res_olympus["nodata_status"] is False
    assert res_olympus["elevation_m"] > 19000

    # Outside latitude boundary (> 88 deg)
    res_out = client.get_elevation_at_point(89.5, 50.0)
    assert res_out["nodata_status"] is True
    assert "outside" in res_out["error"].lower()


def test_raster_window_read():
    """Test reading a small raster sub-window without full dataset loading."""
    client = ZuhuraScienceAccess(repo_root=REPO_ROOT)
    # Read a 10x10 block from global MOLA COG
    arr = client.read_raster_window(
        product_id="mola_global_meg128_cog",
        col_offset=9930,
        row_offset=8911,
        width=10,
        height=10
    )
    assert arr.shape == (10, 10)
    assert arr.dtype.name == "int16"
    assert -3000 <= arr.mean() <= -2000
