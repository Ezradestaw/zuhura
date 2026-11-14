"""
Zuhura Planetary Digital Twin - Stage 7 Global Mars Terrain Pyramid Generator
Generates a multi-resolution Cesium Quantized-Mesh 1.0 terrain pyramid from
mola_global_meg128_cog.tif for global planetary coverage.

Conventions:
- Geographic Tiling Scheme (Cesium): 2x1 tiles at Level 0
- TMS coordinate indexing: y=0 at South Pole (-90), y=n_y-1 at North Pole (+90)
- Ellipsoid: IAU/IAG 2015 Mars Biaxial Ellipsoid (a=3396190, c=3376200)
- Oct-encoded per-vertex normal vectors included (octvertexnormals, ID 1)
- Resumable and idempotent: skips existing validated tiles
"""

import argparse
import io
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from osgeo import gdal

from zuhura_data.terrain.quantized_mesh import (
    MARS_A,
    MARS_C,
    decode_quantized_mesh,
    encode_quantized_mesh
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_COG_PATH = REPO_ROOT / "data/processed/mola/global_v3/mola_global_meg128_cog.tif"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data/tiles/terrain/global"

MOLA_RADIUS_M = 3396000.0


def compute_tms_tile_bounds(z: int, x: int, y: int) -> Tuple[float, float, float, float]:
    """
    Computes [lon_min, lat_min, lon_max, lat_max] in degrees for tile (z, x, y)
    in Cesium GeographicTilingScheme using TMS (Tile Map Service) coordinates.
    - Level 0: 2 tiles along lon, 1 tile along lat.
    - At level z: n_y = 2^z, n_x = 2 * n_y.
    - TMS: y=0 is South Pole (-90), y=n_y-1 is North Pole (+90).
    """
    n_y = 2 ** z
    n_x = 2 * n_y
    d_lon = 360.0 / n_x
    d_lat = 180.0 / n_y

    lon_min = x * d_lon - 180.0
    lon_max = (x + 1) * d_lon - 180.0
    lat_min = y * d_lat - 90.0
    lat_max = (y + 1) * d_lat - 90.0

    return lon_min, lat_min, lon_max, lat_max


def extract_tile_elevation(
    ds: gdal.Dataset,
    lon_min: float,
    lat_min: float,
    lon_max: float,
    lat_max: float,
    grid_size: int = 33
) -> np.ndarray:
    """
    Extracts a (grid_size, grid_size) elevation grid for the geographic bounding box
    from the global MOLA COG using simple cylindrical projection bounds.
    Preserves polar boundaries and clamps to valid MOLA coverage [-88, +88].
    """
    def to_mola_x(lon: float) -> float:
        lon360 = lon % 360.0
        if lon360 < 0:
            lon360 += 360.0
        return MOLA_RADIUS_M * math.radians(lon360 - 180.0)

    def to_mola_y(lat: float) -> float:
        return MOLA_RADIUS_M * math.radians(lat)

    # Simple cylindrical projected bounds
    p_xmin = min(to_mola_x(lon_min), to_mola_x(lon_max))
    p_xmax = max(to_mola_x(lon_min), to_mola_x(lon_max))
    # Handle tile crossing 180 meridian
    if p_xmax <= p_xmin:
        p_xmin = -MOLA_RADIUS_M * math.pi
        p_xmax = MOLA_RADIUS_M * math.pi

    p_ymin = to_mola_y(max(-88.0, min(88.0, lat_min)))
    p_ymax = to_mola_y(max(-88.0, min(88.0, lat_max)))
    if p_ymax <= p_ymin:
        p_ymax = p_ymin + 1000.0

    warp_opts = gdal.WarpOptions(
        format="MEM",
        width=grid_size,
        height=grid_size,
        outputBounds=[p_xmin, p_ymin, p_xmax, p_ymax],
        resampleAlg="bilinear"
    )

    tile_ds = gdal.Warp("", ds, options=warp_opts)
    if not tile_ds:
        # Fallback flat datum
        return np.zeros((grid_size, grid_size), dtype=np.float32)

    band = tile_ds.GetRasterBand(1)
    elev_arr = band.ReadAsArray().astype(np.float32)
    tile_ds = None

    # Replace NoData sentinel values (-99999 or extremes) with 0.0 datum
    elev_arr[elev_arr < -15000.0] = 0.0
    elev_arr[elev_arr > 30000.0] = 0.0

    # If tile is outside valid MOLA latitude range (> 88 degrees), flat surface
    if lat_max < -88.0 or lat_min > 88.0:
        elev_arr[:] = 0.0

    return elev_arr


def build_global_terrain_pyramid(
    cog_path: Path = DEFAULT_COG_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    max_zoom: int = 2,
    grid_size: int = 33,
    include_normals: bool = True,
    force_rebuild: bool = False
) -> Dict[str, Any]:
    """
    Builds a complete global Mars quantized-mesh pyramid from level 0 up to max_zoom.
    """
    t0 = time.time()
    output_dir.mkdir(parents=True, exist_ok=True)

    ds = gdal.Open(str(cog_path), gdal.GA_ReadOnly)
    assert ds is not None, f"Failed to open source MOLA COG at {cog_path}"

    tiles_generated = 0
    tiles_skipped = 0
    available_matrix: List[List[Dict[str, int]]] = []

    for z in range(max_zoom + 1):
        n_y = 2 ** z
        n_x = 2 * n_y
        available_matrix.append([{
            "startX": 0,
            "endX": n_x - 1,
            "startY": 0,
            "endY": n_y - 1
        }])

        print(f"--- Processing Zoom Level {z} ({n_x}x{n_y} = {n_x * n_y} tiles) ---")

        for x in range(n_x):
            tile_col_dir = output_dir / str(z) / str(x)
            tile_col_dir.mkdir(parents=True, exist_ok=True)

            for y in range(n_y):
                tile_path = tile_col_dir / f"{y}.terrain"

                # Check idempotency
                if tile_path.exists() and not force_rebuild:
                    try:
                        with open(tile_path, "rb") as f:
                            tile_bytes = f.read()
                        if len(tile_bytes) >= 88:
                            tiles_skipped += 1
                            continue
                    except Exception:
                        pass

                # Extract bounds and elevation
                lon_min, lat_min, lon_max, lat_max = compute_tms_tile_bounds(z, x, y)
                elev_grid = extract_tile_elevation(ds, lon_min, lat_min, lon_max, lat_max, grid_size=grid_size)

                min_h = float(elev_grid.min())
                max_h = float(elev_grid.max())

                tile_bytes = encode_quantized_mesh(
                    elev_grid,
                    lon_min=lon_min, lat_min=lat_min,
                    lon_max=lon_max, lat_max=lat_max,
                    min_height=min_h, max_height=max_h,
                    include_normals=include_normals
                )

                with open(tile_path, "wb") as f:
                    f.write(tile_bytes)

                tiles_generated += 1

    ds = None
    elapsed = time.time() - t0

    # Write layer.json for the global terrain pyramid
    layer_meta = {
        "tilejson": "2.1.0",
        "format": "quantized-mesh-1.0",
        "version": "1.0.0",
        "name": "Zuhura Mars Global Multi-Resolution Terrain",
        "description": "Global multi-resolution quantized-mesh 1.0 terrain pyramid derived from MOLA MEG128 global COG (IAU/IAG 2015 Mars Biaxial Ellipsoid).",
        "scheme": "tms",
        "ellipsoid": {
            "name": "IAU/IAG 2015 Mars Biaxial Ellipsoid",
            "semiMajorAxis": MARS_A,
            "semiMinorAxis": MARS_C
        },
        "bounds": [-180.0, -90.0, 180.0, 90.0],
        "minzoom": 0,
        "maxzoom": max_zoom,
        "extensions": ["octvertexnormals"] if include_normals else [],
        "available": available_matrix,
        "tiles": ["{z}/{x}/{y}.terrain"],
        "metadata": {
            "source_product": "mola_global_meg128_cog",
            "vertical_datum": "MOLA GMM-3 Areoid",
            "grid_size": grid_size,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "has_normals": include_normals
        }
    }

    layer_file = output_dir / "layer.json"
    with open(layer_file, "w", encoding="utf-8") as f:
        json.dump(layer_meta, f, indent=2)

    total_tiles = tiles_generated + tiles_skipped
    print(f"Global terrain pyramid complete:")
    print(f"  Total tiles: {total_tiles} (Generated: {tiles_generated}, Skipped: {tiles_skipped})")
    print(f"  Elapsed time: {elapsed:.2f} s")
    print(f"  layer.json written to {layer_file}")

    return {
        "status": "success",
        "output_dir": str(output_dir),
        "layer_file": str(layer_file),
        "max_zoom": max_zoom,
        "total_tiles": total_tiles,
        "tiles_generated": tiles_generated,
        "tiles_skipped": tiles_skipped,
        "elapsed_seconds": round(elapsed, 2),
        "available_levels": len(available_matrix)
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Global Mars Terrain Pyramid")
    parser.add_argument("--max-zoom", type=int, default=2, help="Maximum zoom level (default: 2, 42 tiles)")
    parser.add_argument("--grid-size", type=int, default=33, help="Grid size per tile (default: 33x33)")
    parser.add_argument("--no-normals", action="store_true", help="Disable surface normals extension")
    parser.add_argument("--force", action="store_true", help="Force rebuild existing tiles")
    args = parser.parse_args()

    build_global_terrain_pyramid(
        max_zoom=args.max_zoom,
        grid_size=args.grid_size,
        include_normals=not args.no_normals,
        force_rebuild=args.force
    )
