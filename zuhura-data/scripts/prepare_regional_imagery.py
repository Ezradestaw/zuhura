#!/usr/bin/env python3
"""
Zuhura Planetary Digital Twin - Regional & Local Imagery Preparation
Prepares georeferenced Cloud-Optimized GeoTIFFs for:
  1. CTX Jezero EDR Swath (P02_001820_1984, 5.55 m/px)
  2. HiRISE Perseverance Landing Site (PSP_004299_1985_MRGB, ~0.5 m/px)
Applies strict geodetic ground control points from official PDS ODE catalogs,
radiometric contrast normalization, and multi-scale internal overviews.
"""

import json
import math
from pathlib import Path
import numpy as np
from osgeo import gdal, osr

REPO_ROOT = Path("/home/anonymous/Zuhura")
DATA_DIR = REPO_ROOT / "zuhura-data/data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

MARS_RADIUS_M = 3396190.0

def get_mars_srs():
    srs = osr.SpatialReference()
    # IAU 2015 Mars Equidistant Cylindrical
    srs.ImportFromProj4(f"+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=0 +R={MARS_RADIUS_M} +units=m +no_defs")
    return srs

def prepare_ctx_jezero():
    print("\n--- Preparing CTX Jezero GeoTIFF ---")
    ctx_raw_path = RAW_DIR / "ctx/P02_001820_1984_XI_18N282W.IMG"
    out_tif = PROCESSED_DIR / "ctx/P02_001820_1984_jezero_ctx_5m_cog.tif"
    out_tif.parent.mkdir(parents=True, exist_ok=True)
    
    ds_raw = gdal.Open(str(ctx_raw_path))
    w = ds_raw.RasterXSize
    h = ds_raw.RasterYSize
    print(f"CTX raw dimensions: {w} x {h}")
    
    # Read raw 8-bit pixel data and perform percentile contrast stretch
    band = ds_raw.GetRasterBand(1)
    arr = band.ReadAsArray()
    
    # 1% to 99% contrast stretch
    valid_pixels = arr[arr > 0]
    p1, p99 = np.percentile(valid_pixels, (1.0, 99.0))
    stretched = np.clip((arr.astype(np.float32) - p1) / (p99 - p1), 0.0, 1.0) * 255.0
    stretched[arr == 0] = 0 # keep nodata
    stretched = stretched.astype(np.uint8)
    
    # Write intermediate GeoTIFF with GCPs
    mem_driver = gdal.GetDriverByName("MEM")
    mem_ds = mem_driver.Create("", w, h, 1, gdal.GDT_Byte)
    mem_ds.GetRasterBand(1).WriteArray(stretched)
    mem_ds.GetRasterBand(1).SetNoDataValue(0)
    
    # GCPs from official PDS ODE Footprint geometry:
    # POLYGON ((77.53 18.654, 77.62 17.9408, 77.13 17.8814, 77.04 18.5946, 77.53 18.654))
    # Top-Left: (0, 0) -> (77.04, 18.5946)
    # Top-Right: (w, 0) -> (77.53, 18.654)
    # Bottom-Right: (w, h) -> (77.62, 17.9408)
    # Bottom-Left: (0, h) -> (77.13, 17.8814)
    # Center: (w/2, h/2) -> (77.3296, 18.2678)
    gcps = [
        gdal.GCP(77.04, 18.5946, 0.0, 0, 0),
        gdal.GCP(77.53, 18.6540, 0.0, w, 0),
        gdal.GCP(77.62, 17.9408, 0.0, w, h),
        gdal.GCP(77.13, 17.8814, 0.0, 0, h),
        gdal.GCP(77.3296, 18.2678, 0.0, w/2, h/2)
    ]
    
    srs_geo = osr.SpatialReference()
    srs_geo.ImportFromProj4(f"+proj=longlat +R={MARS_RADIUS_M} +no_defs")
    mem_ds.SetGCPs(gcps, srs_geo.ExportToWkt())
    
    # Warp with polynomial order 1 to north-up Equidistant Cylindrical
    warp_opts = gdal.WarpOptions(
        format="COG",
        dstSRS=srs_geo.ExportToWkt(),
        resampleAlg="bilinear",
        creationOptions=[
            "COMPRESS=DEFLATE",
            "OVERVIEWS=ALL",
            "BLOCKSIZE=512",
            "NUM_THREADS=ALL_CPUS"
        ]
    )
    gdal.Warp(str(out_tif), mem_ds, options=warp_opts)
    print(f"CTX GeoTIFF created at: {out_tif} ({out_tif.stat().st_size / (1024*1024):.2f} MB)")
    ds_raw = None
    mem_ds = None

def prepare_hirise_jezero():
    print("\n--- Preparing HiRISE Jezero GeoTIFF ---")
    hirise_raw_path = RAW_DIR / "hirise/PSP_004299_1985_MRGB.abrowse.jpg"
    out_tif = PROCESSED_DIR / "hirise/PSP_004299_1985_jezero_hirise_cog.tif"
    out_tif.parent.mkdir(parents=True, exist_ok=True)
    
    ds_raw = gdal.Open(str(hirise_raw_path))
    w = ds_raw.RasterXSize
    h = ds_raw.RasterYSize
    bands = ds_raw.RasterCount
    print(f"HiRISE raw dimensions: {w} x {h}, bands: {bands}")
    
    # Read RGB bands
    arr = ds_raw.ReadAsArray()
    
    mem_driver = gdal.GetDriverByName("MEM")
    mem_ds = mem_driver.Create("", w, h, bands, gdal.GDT_Byte)
    for b in range(bands):
        mem_ds.GetRasterBand(b + 1).WriteArray(arr[b])
    
    # GCPs from official PDS ODE KML Footprint:
    # 77.6537,18.2996 (bottom-right)
    # 77.5531,18.2876 (bottom-left)
    # 77.5158,18.5714 (top-left)
    # 77.6166,18.5834 (top-right)
    gcps = [
        gdal.GCP(77.5158, 18.5714, 0.0, 0, 0),
        gdal.GCP(77.6166, 18.5834, 0.0, w, 0),
        gdal.GCP(77.6537, 18.2996, 0.0, w, h),
        gdal.GCP(77.5531, 18.2876, 0.0, 0, h),
        gdal.GCP(77.5848, 18.4355, 0.0, w/2, h/2) # center point
    ]
    
    srs_geo = osr.SpatialReference()
    srs_geo.ImportFromProj4(f"+proj=longlat +R={MARS_RADIUS_M} +no_defs")
    mem_ds.SetGCPs(gcps, srs_geo.ExportToWkt())
    
    warp_opts = gdal.WarpOptions(
        format="COG",
        dstSRS=srs_geo.ExportToWkt(),
        resampleAlg="bilinear",
        creationOptions=[
            "COMPRESS=JPEG",
            "QUALITY=90",
            "OVERVIEWS=ALL",
            "BLOCKSIZE=512",
            "NUM_THREADS=ALL_CPUS"
        ]
    )
    gdal.Warp(str(out_tif), mem_ds, options=warp_opts)
    print(f"HiRISE GeoTIFF created at: {out_tif} ({out_tif.stat().st_size / (1024*1024):.2f} MB)")
    ds_raw = None
    mem_ds = None

if __name__ == "__main__":
    prepare_ctx_jezero()
    prepare_hirise_jezero()
