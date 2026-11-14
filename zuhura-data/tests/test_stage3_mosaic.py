"""
Tests for Stage 3 Global MOLA Mosaic (VRT & COG).
Validates dimensions, bounds, pixel size, CRS, data type, NoData policy,
COG compliance, overviews, and sample equivalence.
"""

from pathlib import Path
import numpy as np
import pytest
from osgeo import gdal
from osgeo_utils.samples.validate_cloud_optimized_geotiff import validate as validate_cog

REPO_ROOT = Path(__file__).resolve().parent.parent
GLOBAL_V3_DIR = REPO_ROOT / "data/processed/mola/global_v3"
VRT_PATH = GLOBAL_V3_DIR / "mola_global_meg128.vrt"
COG_PATH = GLOBAL_V3_DIR / "mola_global_meg128_cog.tif"
TILES_V2_DIR = REPO_ROOT / "data/processed/mola/meg128_v2"

EXPECTED_WIDTH = 46080
EXPECTED_HEIGHT = 22528
EXPECTED_ORIGIN_X = -10668848.652288001
EXPECTED_ORIGIN_Y = 5215881.563340800
EXPECTED_PIXEL_SIZE = 463.0576672


def test_vrt_exists_and_geometry():
    """Validate global VRT geometry, CRS, dimensions, and NoData policy."""
    assert VRT_PATH.exists(), f"Missing VRT file: {VRT_PATH}"

    ds = gdal.Open(str(VRT_PATH))
    assert ds.RasterXSize == EXPECTED_WIDTH
    assert ds.RasterYSize == EXPECTED_HEIGHT

    band = ds.GetRasterBand(1)
    assert gdal.GetDataTypeName(band.DataType) == "Int16"
    assert band.GetNoDataValue() is None

    gt = ds.GetGeoTransform()
    assert abs(gt[0] - EXPECTED_ORIGIN_X) < 1e-3
    assert abs(gt[3] - EXPECTED_ORIGIN_Y) < 1e-3
    assert abs(gt[1] - EXPECTED_PIXEL_SIZE) < 1e-3
    assert abs(gt[5] - (-EXPECTED_PIXEL_SIZE)) < 1e-3


def test_vrt_relative_paths():
    """Verify that VRT uses relative paths to source tiles."""
    with open(VRT_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert 'relativeToVRT="1"' in content
    assert "../meg128_v2/" in content


def test_cog_exists_and_compliance():
    """Validate COG compliance using official GDAL COG layout validator."""
    assert COG_PATH.exists(), f"Missing COG file: {COG_PATH}"
    assert COG_PATH.stat().st_size > 500 * 1024 * 1024  # > 500 MB

    warnings, errors, details = validate_cog(str(COG_PATH))
    assert len(errors) == 0, f"COG validation errors: {errors}"


def test_cog_overviews_and_nodata():
    """Verify COG has required overview levels (2..64) and NoData=None."""
    ds = gdal.Open(str(COG_PATH))
    band = ds.GetRasterBand(1)

    assert band.GetNoDataValue() is None
    assert gdal.GetDataTypeName(band.DataType) == "Int16"

    ovr_count = band.GetOverviewCount()
    assert ovr_count >= 6, f"Expected at least 6 overviews (factors 2,4,8,16,32,64), found {ovr_count}"

    # Verify overview downsampling dimensions
    factors = [ds.RasterXSize / band.GetOverview(i).XSize for i in range(ovr_count)]
    expected_factors = [2, 4, 8, 16, 32, 64]
    for exp_f in expected_factors:
        assert any(abs(f - exp_f) < 0.2 for f in factors), f"Missing overview factor {exp_f}"


def test_cog_tile_pixel_equivalence():
    """Verify pixel equivalence between source tiles and COG mosaic."""
    ds_cog = gdal.Open(str(COG_PATH))
    cog_band = ds_cog.GetRasterBand(1)

    # Check a test window in megt00n180hb (row 2, col 2)
    # Offsets: col 2 -> 2 * 11520 = 23040; row 2 -> 2 * 5632 = 11264
    tile_ds = gdal.Open(str(TILES_V2_DIR / "megt00n180hb.tif"))
    tile_band = tile_ds.GetRasterBand(1)

    tile_sample = tile_band.ReadAsArray(2000, 2000, 100, 100)
    cog_sample = cog_band.ReadAsArray(23040 + 2000, 11264 + 2000, 100, 100)

    assert np.array_equal(tile_sample, cog_sample), "Pixel values differ between source tile and COG"
