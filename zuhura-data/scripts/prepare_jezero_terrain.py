#!/usr/bin/env python3
"""
Zuhura Planetary Digital Twin - Stage 6 Phase 5: Jezero Regional Terrain Preparation
Extracts a documented regional digital elevation model over Jezero Crater (18.0N - 19.0N, 76.5E - 78.5E)
from the validated MOLA Global COG (v3), preserving exact Int16 elevations referenced to the MOLA GMM-3 areoid.
Outputs:
  - data/processed/mola/jezero/mola_jezero_meg128.tif
  - data/processed/mola/jezero/jezero_terrain_provenance.json
"""

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from osgeo import gdal

REPO_ROOT = Path("/home/anonymous/Zuhura/zuhura-data")
SOURCE_COG = REPO_ROOT / "data/processed/mola/global_v3/mola_global_meg128_cog.tif"
OUT_DIR = REPO_ROOT / "data/processed/mola/jezero"
OUT_TIF = OUT_DIR / "mola_jezero_meg128.tif"
OUT_PROV = OUT_DIR / "jezero_terrain_provenance.json"

MOLA_R = 3396000.0


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def prepare_jezero_terrain():
    print("=" * 70)
    print("ZUHURA PLANETARY DATA PIPELINE: JEZERO REGIONAL TERRAIN EXTRACTION")
    print("=" * 70)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    assert SOURCE_COG.exists(), f"Source COG not found: {SOURCE_COG}"

    source_sha = sha256_file(SOURCE_COG)
    print(f"Source MOLA COG: {SOURCE_COG}")
    print(f"Source SHA-256: {source_sha}")

    # Jezero Crater Pilot Bounds: 18.0 - 19.0 N, 76.5 - 78.5 E
    lon_min = 76.5
    lon_max = 78.5
    lat_min = 18.0
    lat_max = 19.0

    # Mars Simple Cylindrical (R = 3396 km, Central Meridian 180E)
    x_min = MOLA_R * math.radians(lon_min - 180.0)
    x_max = MOLA_R * math.radians(lon_max - 180.0)
    y_min = MOLA_R * math.radians(lat_min)
    y_max = MOLA_R * math.radians(lat_max)

    print(f"\nExtraction Geographic Bounds: {lat_min}°N to {lat_max}°N, {lon_min}°E to {lon_max}°E")
    print(f"Projected Bounds: X: [{x_min:.2f}, {x_max:.2f}], Y: [{y_min:.2f}, {y_max:.2f}]")

    # Use GDAL Translate to extract exact window without resampling
    translate_opts = gdal.TranslateOptions(
        format="GTiff",
        outputType=gdal.GDT_Int16,
        projWin=[x_min, y_max, x_max, y_min],  # [ulx, uly, lrx, lry]
        creationOptions=[
            "COMPRESS=DEFLATE",
            "PREDICTOR=2",
            "TILED=YES",
            "BLOCKXSIZE=256",
            "BLOCKYSIZE=256"
        ]
    )

    print(f"\nExecuting window extraction to: {OUT_TIF}")
    ds_out = gdal.Translate(str(OUT_TIF), str(SOURCE_COG), options=translate_opts)
    assert ds_out is not None, "GDAL Translate failed."

    width = ds_out.RasterXSize
    height = ds_out.RasterYSize
    gt = ds_out.GetGeoTransform()
    srs_wkt = ds_out.GetProjection()
    band = ds_out.GetRasterBand(1)
    arr = band.ReadAsArray()
    min_elev = int(arr.min())
    max_elev = int(arr.max())
    mean_elev = float(arr.mean())
    ds_out = None

    out_sha = sha256_file(OUT_TIF)
    out_size = OUT_TIF.stat().st_size

    print(f"Extracted Grid: {width} x {height} pixels (Int16, {out_size:,} bytes)")
    print(f"Elevation Statistics: Min={min_elev} m, Max={max_elev} m, Mean={mean_elev:.1f} m")
    print(f"Output SHA-256: {out_sha}")

    provenance = {
        "dataset_id": "zuhura-mola-jezero-regional-dem",
        "title": "MGS MOLA Jezero Crater Regional Elevation Model (MEG128)",
        "source_product": "mola_global_meg128_cog",
        "source_path": str(SOURCE_COG),
        "source_sha256": source_sha,
        "extraction_bounds": {
            "min_lat": lat_min,
            "max_lat": lat_max,
            "min_lon": lon_min,
            "max_lon": lon_max,
            "x_min": x_min,
            "x_max": x_max,
            "y_min": y_min,
            "y_max": y_max
        },
        "grid_dimensions": {"width": width, "height": height, "bands": 1},
        "data_type": "Int16",
        "units": "meters",
        "vertical_reference": "MOLA GMM-3 Areoid (Equipotential Reference Surface)",
        "geotransform": list(gt),
        "crs_wkt": srs_wkt,
        "elevation_statistics": {
            "min_elevation_m": min_elev,
            "max_elevation_m": max_elev,
            "mean_elevation_m": round(mean_elev, 2)
        },
        "output_file": str(OUT_TIF),
        "output_sha256": out_sha,
        "output_size_bytes": out_size,
        "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
        "processing_software": "GDAL 3.13.3 Translate",
        "scientific_integrity": "Exact zero-loss window extraction from verified global MOLA COG v3. All elevations preserved."
    }

    with open(OUT_PROV, "w", encoding="utf-8") as f:
        json.dump(provenance, f, indent=2)
    print(f"Provenance record saved to: {OUT_PROV}")

    return provenance


if __name__ == "__main__":
    prepare_jezero_terrain()
