"""
Zuhura Planetary Digital Twin - Stage 7 Regional Terrain Refinement Generator
Extracts regional DEMs from mola_global_meg128_cog.tif and builds targeted
Quantized-Mesh 1.0 terrain models for:
  1. Jezero Crater (Perseverance site, 18-19 N, 76.5-78.5 E)
  2. Gale Crater (Curiosity / Mt Sharp, -5.5 to -4.0 N, 137.0-138.5 E)
  3. Valles Marineris (Canyon system, -14.0 to -5.0 N, 280.0-295.0 E)
  4. Olympus Mons (Caldera and flanks, 15.0-22.0 N, 222.0-232.0 E)
"""

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import numpy as np
from osgeo import gdal

from zuhura_data.terrain.quantized_mesh import (
    MARS_A,
    MARS_C,
    decode_quantized_mesh,
    encode_quantized_mesh
)

REPO_ROOT = Path(__file__).resolve().parent.parent
COG_PATH = REPO_ROOT / "data/processed/mola/global_v3/mola_global_meg128_cog.tif"
REGIONAL_DEM_DIR = REPO_ROOT / "data/processed/mola/regional"
TILES_BASE_DIR = REPO_ROOT / "data/tiles/terrain"

MOLA_RADIUS_M = 3396000.0

REGIONS = {
    "jezero": {
        "title": "Jezero Crater",
        "description": "Perseverance landing site, western fan delta and ancient lacustrine basin.",
        "bbox": [76.5, 18.0, 78.5, 19.0],  # [min_lon, min_lat, max_lon, max_lat]
        "zoom": 9,
        "grid_size": 33
    },
    "gale": {
        "title": "Gale Crater & Mount Sharp",
        "description": "Curiosity rover traverse, central mound Aeolis Mons and layered sulfate sulfate strata.",
        "bbox": [137.0, -5.5, 138.5, -4.0],
        "zoom": 9,
        "grid_size": 33
    },
    "valles_marineris": {
        "title": "Valles Marineris (Coprates & Melas Chasma)",
        "description": "Massive tectonic rift canyon system descending over 7 km below datum.",
        "bbox": [280.0, -14.0, 295.0, -5.0],
        "zoom": 7,
        "grid_size": 65
    },
    "olympus_mons": {
        "title": "Olympus Mons Volcano",
        "description": "Solar system's highest volcano rising to +21.2 km with massive summit caldera and basal scarp.",
        "bbox": [222.0, 15.0, 232.0, 22.0],
        "zoom": 7,
        "grid_size": 65
    }
}


def to_mola_x(lon: float) -> float:
    lon360 = lon % 360.0
    if lon360 < 0:
        lon360 += 360.0
    return MOLA_RADIUS_M * math.radians(lon360 - 180.0)


def to_mola_y(lat: float) -> float:
    return MOLA_RADIUS_M * math.radians(lat)


def extract_regional_dem(name: str, config: Dict[str, Any], cog_ds: gdal.Dataset) -> Path:
    """Extracts high-resolution Int16 DEM GeoTIFF for region."""
    min_lon, min_lat, max_lon, max_lat = config["bbox"]
    out_dir = REGIONAL_DEM_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_dem = out_dir / f"mola_{name}_meg128.tif"
    out_prov = out_dir / f"{name}_terrain_provenance.json"

    # Compute pixel width and height at 128 px/deg
    width_px = int(round((max_lon - min_lon) * 128.0))
    height_px = int(round((max_lat - min_lat) * 128.0))

    p_xmin = min(to_mola_x(min_lon), to_mola_x(max_lon))
    p_xmax = max(to_mola_x(min_lon), to_mola_x(max_lon))
    p_ymin = min(to_mola_y(min_lat), to_mola_y(max_lat))
    p_ymax = max(to_mola_y(min_lat), to_mola_y(max_lat))

    warp_opts = gdal.WarpOptions(
        format="GTiff",
        width=width_px,
        height=height_px,
        outputBounds=[p_xmin, p_ymin, p_xmax, p_ymax],
        resampleAlg="bilinear",
        outputType=gdal.GDT_Int16,
        creationOptions=["COMPRESS=DEFLATE", "TILED=YES"]
    )

    gdal.Warp(str(out_dem), cog_ds, options=warp_opts)

    # Read extracted range
    dem_ds = gdal.Open(str(out_dem), gdal.GA_ReadOnly)
    band = dem_ds.GetRasterBand(1)
    arr = band.ReadAsArray()
    min_elev = int(arr.min())
    max_elev = int(arr.max())
    dem_ds = None

    # Write provenance record
    prov = {
        "activity": f"Stage 7 Regional DEM Extraction: {config['title']}",
        "region": name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_dataset": "mola_global_meg128_cog.tif",
        "output_dem": str(out_dem.relative_to(REPO_ROOT)),
        "bounding_box_east": config["bbox"],
        "dimensions": [width_px, height_px],
        "pixel_resolution_m": 463.0577,
        "elevation_range_m": [min_elev, max_elev],
        "vertical_datum": "MOLA GMM-3 Areoid",
        "projection": "Mars_simpCyl_c180"
    }

    with open(out_prov, "w", encoding="utf-8") as f:
        json.dump(prov, f, indent=2)

    print(f"Extracted DEM for {config['title']}: {width_px}x{height_px} px, elev=[{min_elev}, {max_elev}] m")
    return out_dem


def generate_regional_terrain_pyramid(
    name: str,
    config: Dict[str, Any],
    dem_path: Path
) -> Dict[str, Any]:
    """Generates quantized-mesh tiles and layer.json for a specific region."""
    min_lon, min_lat, max_lon, max_lat = config["bbox"]
    zoom = config["zoom"]
    grid_size = config["grid_size"]

    tiles_dir = TILES_BASE_DIR / name
    tiles_dir.mkdir(parents=True, exist_ok=True)

    ds = gdal.Open(str(dem_path), gdal.GA_ReadOnly)
    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray().astype(np.float32)
    ds = None

    min_h = float(arr.min())
    max_h = float(arr.max())

    # Subsample or interpolate to grid_size x grid_size
    from PIL import Image
    im = Image.fromarray(arr)
    im_resized = im.resize((grid_size, grid_size), Image.Resampling.BILINEAR)
    grid_elev = np.array(im_resized, dtype=np.float32)

    # Tile coordinate computation in TMS
    n_y = 2 ** zoom
    n_x = 2 * n_y
    d_lon = 360.0 / n_x
    d_lat = 180.0 / n_y

    mid_lon = (min_lon + max_lon) / 2.0
    mid_lat = (min_lat + max_lat) / 2.0

    x_tile = int((mid_lon + 180.0) / d_lon)
    y_tms = int((mid_lat - (-90.0)) / d_lat)
    y_xyz = int((90.0 - mid_lat) / d_lat)

    tile_bytes = encode_quantized_mesh(
        grid_elev,
        lon_min=min_lon, lat_min=min_lat,
        lon_max=max_lon, lat_max=max_lat,
        min_height=min_h, max_height=max_h,
        include_normals=True
    )

    tile_dir = tiles_dir / str(zoom) / str(x_tile)
    tile_dir.mkdir(parents=True, exist_ok=True)

    # Save TMS tile
    tms_tile_file = tile_dir / f"{y_tms}.terrain"
    with open(tms_tile_file, "wb") as f:
        f.write(tile_bytes)

    # Also save XYZ tile for backward compatibility
    xyz_tile_file = tile_dir / f"{y_xyz}.terrain"
    with open(xyz_tile_file, "wb") as f:
        f.write(tile_bytes)

    # Write regional layer.json
    layer_meta = {
        "tilejson": "2.1.0",
        "format": "quantized-mesh-1.0",
        "version": "1.0.0",
        "name": f"Zuhura Mars Terrain — {config['title']}",
        "description": config["description"],
        "scheme": "tms",
        "ellipsoid": {
            "name": "IAU/IAG 2015 Mars Biaxial Ellipsoid",
            "semiMajorAxis": MARS_A,
            "semiMinorAxis": MARS_C
        },
        "bounds": config["bbox"],
        "minzoom": 0,
        "maxzoom": zoom,
        "extensions": ["octvertexnormals"],
        "available": [
            [{"startX": 0, "endX": 1, "startY": 0, "endY": 0}],
            [{"startX": x_tile, "endX": x_tile, "startY": y_tms, "endY": y_tms}]
        ],
        "tiles": ["{z}/{x}/{y}.terrain"],
        "metadata": {
            "region": name,
            "elevation_range_m": [min_h, max_h],
            "tile_coords": {"z": zoom, "x": x_tile, "y_tms": y_tms, "y_xyz": y_xyz},
            "tile_bytes": len(tile_bytes),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    }

    layer_file = tiles_dir / "layer.json"
    with open(layer_file, "w", encoding="utf-8") as f:
        json.dump(layer_meta, f, indent=2)

    return {
        "region": name,
        "title": config["title"],
        "dem_file": str(dem_path.relative_to(REPO_ROOT)),
        "tms_tile": str(tms_tile_file.relative_to(REPO_ROOT)),
        "layer_file": str(layer_file.relative_to(REPO_ROOT)),
        "tile_bytes": len(tile_bytes),
        "elevation_range_m": [min_h, max_h],
        "zoom": zoom,
        "tile_coords": {"z": zoom, "x": x_tile, "y": y_tms}
    }


def main():
    print("--- Starting Stage 7 Regional Terrain Processing ---")
    cog_ds = gdal.Open(str(COG_PATH), gdal.GA_ReadOnly)
    assert cog_ds is not None, f"Missing COG at {COG_PATH}"

    results = {}
    for name, config in REGIONS.items():
        dem_path = extract_regional_dem(name, config, cog_ds)
        res = generate_regional_terrain_pyramid(name, config, dem_path)
        results[name] = res

    cog_ds = None
    print("All 4 regional terrain models generated successfully!")
    return results


if __name__ == "__main__":
    main()
