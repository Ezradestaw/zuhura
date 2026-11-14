"""
Tests for Stage 2 MOLA processing and Viking quarantine.
Validates zero-elevation preservation, NoData removal, polar scaling, and manifest integrity.
"""

import json
from pathlib import Path
import numpy as np
import pytest
from osgeo import gdal

REPO_ROOT = Path(__file__).resolve().parent.parent
MEG128_V1_DIR = REPO_ROOT / "data/processed/mola/meg128"
MEG128_V2_DIR = REPO_ROOT / "data/processed/mola/meg128_v2"
POLAR_RAW_DIR = REPO_ROOT / "data/raw/mola/polar"
POLAR_V2_DIR = REPO_ROOT / "data/processed/mola/polar_v2"
VIKING_QUARANTINE_DIR = REPO_ROOT / "data/raw/viking/quarantine"
VIKING_RAW_DIR = REPO_ROOT / "data/raw/viking/mdim21"

GLOBAL_TILE_IDS = [
    "megt88n000hb", "megt88n090hb", "megt88n180hb", "megt88n270hb",
    "megt44n000hb", "megt44n090hb", "megt44n180hb", "megt44n270hb",
    "megt00n000hb", "megt00n090hb", "megt00n180hb", "megt00n270hb",
    "megt44s000hb", "megt44s090hb", "megt44s180hb", "megt44s270hb",
]


def test_global_all_16_tiles_exist():
    """Verify all 16 corrected global GeoTIFFs exist in meg128_v2."""
    for tile_id in GLOBAL_TILE_IDS:
        tif_path = MEG128_V2_DIR / f"{tile_id}.tif"
        assert tif_path.exists(), f"Missing corrected tile: {tif_path}"
        assert tif_path.stat().st_size > 0


def test_global_nodata_is_none():
    """Verify NoData value is None for all 16 corrected global tiles."""
    for tile_id in GLOBAL_TILE_IDS:
        tif_path = MEG128_V2_DIR / f"{tile_id}.tif"
        ds = gdal.Open(str(tif_path))
        band = ds.GetRasterBand(1)
        assert band.GetNoDataValue() is None, f"Tile {tile_id} still has NoData tag: {band.GetNoDataValue()}"


def test_global_zero_elevation_preservation():
    """Verify exactly 136,772 zero-elevation pixels are retained across the 16 global tiles."""
    total_zeros = 0
    for tile_id in GLOBAL_TILE_IDS:
        tif_path = MEG128_V2_DIR / f"{tile_id}.tif"
        ds = gdal.Open(str(tif_path))
        arr = ds.GetRasterBand(1).ReadAsArray()
        total_zeros += int(np.count_nonzero(arr == 0))

    assert total_zeros == 136772, f"Expected 136,772 zero-elevation pixels, found {total_zeros}"


def test_global_pixel_by_pixel_exact_match():
    """Verify pixel-by-pixel equality between source and corrected global tiles."""
    # Compare representative tiles from northern, equatorial, and southern bands
    for tile_id in ["megt88n000hb", "megt44n180hb", "megt00n000hb", "megt44s270hb"]:
        v1_path = MEG128_V1_DIR / f"{tile_id}.tif"
        v2_path = MEG128_V2_DIR / f"{tile_id}.tif"

        ds_v1 = gdal.Open(str(v1_path))
        ds_v2 = gdal.Open(str(v2_path))

        arr_v1 = ds_v1.GetRasterBand(1).ReadAsArray()
        arr_v2 = ds_v2.GetRasterBand(1).ReadAsArray()

        assert np.array_equal(arr_v1, arr_v2), f"Pixel values differ for {tile_id}"
        assert ds_v1.GetGeoTransform() == ds_v2.GetGeoTransform()


def test_polar_scaling_and_masking():
    """Verify polar products are Float32, correctly scaled, with DN=0 as NoData=-99999.0."""
    for prod_id in ["megt_n_128_1", "megt_s_128_1"]:
        v2_path = POLAR_V2_DIR / f"{prod_id}.tif"
        assert v2_path.exists(), f"Polar output missing: {v2_path}"

        ds_v2 = gdal.Open(str(v2_path))
        assert ds_v2.RasterXSize == 10240
        assert ds_v2.RasterYSize == 10240

        band = ds_v2.GetRasterBand(1)
        assert gdal.GetDataTypeName(band.DataType) == "Float32"
        assert band.GetNoDataValue() == -99999.0

        # Read small sample window to check scaling formula
        raw_ds = gdal.Open(str(POLAR_RAW_DIR / f"{prod_id}.img"))
        raw_band = raw_ds.GetRasterBand(1)

        raw_sample = raw_band.ReadAsArray(4000, 4000, 200, 200)
        v2_sample = band.ReadAsArray(4000, 4000, 200, 200)

        valid_mask = (raw_sample != 0)
        expected_sample = (raw_sample[valid_mask].astype(np.float32) * 0.25) - 8000.0
        actual_sample = v2_sample[valid_mask]

        assert np.allclose(actual_sample, expected_sample, atol=1e-4)


def test_viking_quarantine_integrity():
    """Verify quarantine manifest exists, complete BigTIFF is untouched, and corrupted files moved."""
    manifest_file = VIKING_QUARANTINE_DIR / "quarantine_manifest.json"
    assert manifest_file.exists(), "Quarantine manifest missing"

    with open(manifest_file, "r") as f:
        data = json.load(f)

    assert len(data["quarantined_files"]) == 2
    for entry in data["quarantined_files"]:
        q_path = Path(entry["quarantine_path"])
        assert q_path.exists(), f"Quarantined file missing on disk: {q_path}"
        assert q_path.stat().st_size == entry["file_size_bytes"]

    # Verify complete BigTIFF is preserved
    complete_bigtiff = VIKING_RAW_DIR / "Mars_Viking_MDIM21_ClrMosaic_global_232m.tiff"
    assert complete_bigtiff.exists()
    assert complete_bigtiff.stat().st_size == 12742411029
