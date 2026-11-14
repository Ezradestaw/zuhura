"""
Map tile endpoints served from Cloud Optimized GeoTIFFs.
Provides on-the-fly rendering of Cloud-Optimized GeoTIFFs into PNG map tiles
compatible with CesiumJS GeographicTilingScheme and Web Mercator XYZ clients.
Includes tile disk caching, scientific colormaps, and NoData transparency.
"""

import io
import json
import math
from pathlib import Path
from typing import Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
import matplotlib
import matplotlib.cm as cm
import numpy as np
from osgeo import gdal
from PIL import Image

from zuhura.api.deps import get_science_access
from zuhura.core.config import settings
from zuhura_data.access.client import ZuhuraScienceAccess

router = APIRouter()

MOLA_RADIUS_M = 3396000.0
MARS_RADIUS_M = 3396190.0

_TRANSPARENT_PNG: Optional[bytes] = None
_viking_ds = None
_ctx_ds = None
_hirise_ds = None


def get_transparent_tile_png() -> bytes:
    """Returns cached 256x256 transparent RGBA PNG bytes."""
    global _TRANSPARENT_PNG
    if _TRANSPARENT_PNG is None:
        img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        _TRANSPARENT_PNG = buf.getvalue()
    return _TRANSPARENT_PNG


def get_viking_ds(repo_root: Path):
    """Singleton getter for Viking MDIM 2.1 COG dataset."""
    global _viking_ds
    if _viking_ds is None:
        p = repo_root / "data/processed/viking/Mars_Viking_MDIM21_ClrMosaic_global_232m_cog.tif"
        if p.exists():
            _viking_ds = gdal.Open(str(p))
    return _viking_ds


def get_ctx_ds(repo_root: Path):
    """Singleton getter for CTX Jezero GeoTIFF dataset."""
    global _ctx_ds
    if _ctx_ds is None:
        p = repo_root / "data/processed/ctx/P02_001820_1984_jezero_ctx_5m_cog.tif"
        if p.exists():
            _ctx_ds = gdal.Open(str(p))
    return _ctx_ds


def get_hirise_ds(repo_root: Path):
    """Singleton getter for HiRISE Jezero GeoTIFF dataset."""
    global _hirise_ds
    if _hirise_ds is None:
        p = repo_root / "data/processed/hirise/PSP_004299_1985_jezero_hirise_cog.tif"
        if p.exists():
            _hirise_ds = gdal.Open(str(p))
    return _hirise_ds


def compute_tile_bounds(
    z: int, x: int, y: int, scheme: str = "geographic"
) -> Tuple[float, float, float, float]:
    """
    Computes [lon_min, lat_min, lon_max, lat_max] in degrees for tile (z, x, y).
    - geographic: Cesium GeographicTilingScheme (Level 0 has 2x1 tiles across 360x180)
    - webmercator: Standard Web Mercator (EPSG:3857)
    """
    if scheme == "webmercator":
        n = 2.0 ** z
        lon_min = x / n * 360.0 - 180.0
        lon_max = (x + 1) / n * 360.0 - 180.0
        lat_rad_max = math.atan(math.sinh(math.pi * (1.0 - 2.0 * y / n)))
        lat_rad_min = math.atan(math.sinh(math.pi * (1.0 - 2.0 * (y + 1) / n)))
        lat_min = math.degrees(lat_rad_min)
        lat_max = math.degrees(lat_rad_max)
        return lon_min, lat_min, lon_max, lat_max
    else:
        # Cesium GeographicTilingScheme:
        # At zoom level z:
        # X tiles: 2 * 2^z
        # Y tiles: 1 * 2^z
        n_y = 2.0 ** z
        n_x = 2.0 * n_y
        d_lon = 360.0 / n_x
        d_lat = 180.0 / n_y
        lon_min = x * d_lon - 180.0
        lon_max = (x + 1) * d_lon - 180.0
        lat_max = 90.0 - y * d_lat
        lat_min = 90.0 - (y + 1) * d_lat
        return lon_min, lat_min, lon_max, lat_max





def _directory_has_entries(path: Path) -> bool:
    if not path.is_dir():
        return False
    try:
        next(path.iterdir())
        return True
    except (StopIteration, OSError):
        return False


@router.get("/source-status", summary="Local tile cache versus remote imagery origin")
async def get_tile_source_status():
    """
    Reports whether imagery and terrain tiles are present on the local cache
    used by the globe, or would have to be fetched from remote NASA/USGS services.
    """
    cache_root = Path(settings.TILES_CACHE_DIR)
    layers = {
        "viking": cache_root / "viking",
        "ctx": cache_root / "ctx",
        "hirise": cache_root / "hirise",
        "terrain": cache_root / "terrain",
        "cog_terrain_geographic": cache_root / "cog_terrain_geographic",
    }
    present = {name: _directory_has_entries(path) for name, path in layers.items()}
    cached = sum(1 for ready in present.values() if ready)
    if cached == 0:
        mode = "remote_network"
        imagery_origin = "remote NASA/USGS"
    elif cached == len(present):
        mode = "local_cache"
        imagery_origin = "local disk cache"
    else:
        mode = "mixed"
        imagery_origin = "local cache with remote NASA/USGS fallback"

    return {
        "mode": mode,
        "imagery_origin": imagery_origin,
        "cache_root": str(cache_root),
        "layers": present,
        "remote_providers": ["NASA PDS", "USGS Astrogeology", "NASA Solar System Treks"],
    }


@router.get("/viking/{z}/{x}/{y}.jpg", summary="Global Viking MDIM 2.1 Natural Color Tile")
@router.get("/viking/{z}/{x}/{y}.png", summary="Global Viking MDIM 2.1 Natural Color Tile (PNG)")
async def get_viking_tile(
    z: int,
    x: int,
    y: int,
    scheme: str = Query("geographic", description="Tiling scheme: geographic (Cesium default)"),
    science_access: ZuhuraScienceAccess = Depends(get_science_access)
):
    """
    Renders a natural color Martian surface tile from the USGS Viking MDIM 2.1 global color mosaic.
    Features sub-10ms direct overview reads, high-speed disk caching, and authentic planetary colors.
    """
    if z < 0 or z > 10:
        raise HTTPException(status_code=400, detail="Zoom level must be between 0 and 10.")
    n_y = 2 ** z
    n_x = 2 * n_y
    if x < 0 or x >= n_x or y < 0 or y >= n_y:
        raise HTTPException(status_code=404, detail="Tile index out of range for zoom level.")

    cache_dir = Path(settings.TILES_CACHE_DIR) / "viking" / str(z) / str(x)
    cache_file = cache_dir / f"{y}.jpg"
    if cache_file.exists():
        with open(cache_file, "rb") as f:
            return Response(
                content=f.read(),
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=86400", "X-Tile-Cache": "HIT"}
            )

    ds = get_viking_ds(science_access.repo_root)
    if not ds:
        raise HTTPException(status_code=503, detail="Viking MDIM 2.1 COG dataset unavailable.")

    lon_min, lat_min, lon_max, lat_max = compute_tile_bounds(z, x, y, scheme=scheme)
    gt = ds.GetGeoTransform()

    x_min_proj = MARS_RADIUS_M * math.radians(lon_min)
    x_max_proj = MARS_RADIUS_M * math.radians(lon_max)
    y_min_proj = MARS_RADIUS_M * math.radians(lat_min)
    y_max_proj = MARS_RADIUS_M * math.radians(lat_max)

    px_start = int(round((x_min_proj - gt[0]) / gt[1]))
    px_end = int(round((x_max_proj - gt[0]) / gt[1]))
    py_start = int(round((y_max_proj - gt[3]) / gt[5]))
    py_end = int(round((y_min_proj - gt[3]) / gt[5]))

    px_start = max(0, min(ds.RasterXSize - 1, px_start))
    px_end = max(px_start + 1, min(ds.RasterXSize, px_end))
    py_start = max(0, min(ds.RasterYSize - 1, py_start))
    py_end = max(py_start + 1, min(ds.RasterYSize, py_end))

    read_w = px_end - px_start
    read_h = py_end - py_start

    arr = ds.ReadAsArray(px_start, py_start, read_w, read_h, buf_xsize=256, buf_ysize=256)
    if arr is None or arr.shape[0] < 3:
        raise HTTPException(status_code=500, detail="Failed to read Viking COG tile pixels.")

    rgb = np.transpose(arr[:3], (1, 2, 0))
    img = Image.fromarray(rgb)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    jpg_bytes = buf.getvalue()

    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "wb") as f:
            f.write(jpg_bytes)
    except Exception:
        pass

    return Response(
        content=jpg_bytes,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400", "X-Tile-Cache": "MISS"}
    )


@router.get("/ctx/{z}/{x}/{y}.png", summary="Regional Jezero CTX Context Tile (5.55 m/px)")
async def get_ctx_tile(
    z: int,
    x: int,
    y: int,
    scheme: str = Query("geographic", description="Tiling scheme"),
    science_access: ZuhuraScienceAccess = Depends(get_science_access)
):
    """
    Renders a 5.55 m/pixel regional context tile over Jezero Crater from MRO CTX.
    Returns transparent PNG outside CTX coverage.
    """
    if z < 0 or z > 15:
        return Response(content=get_transparent_tile_png(), media_type="image/png")
    lon_min, lat_min, lon_max, lat_max = compute_tile_bounds(z, x, y, scheme=scheme)

    # Footprint overlap check [77.0399, 17.8815, 77.6199, 18.6541]
    if lon_max < 77.0399 or lon_min > 77.6199 or lat_max < 17.8815 or lat_min > 18.6541:
        return Response(content=get_transparent_tile_png(), media_type="image/png")

    cache_dir = Path(settings.TILES_CACHE_DIR) / "ctx" / str(z) / str(x)
    cache_file = cache_dir / f"{y}.png"
    if cache_file.exists():
        with open(cache_file, "rb") as f:
            return Response(content=f.read(), media_type="image/png", headers={"Cache-Control": "public, max-age=86400", "X-Tile-Cache": "HIT"})

    ds = get_ctx_ds(science_access.repo_root)
    if not ds:
        return Response(content=get_transparent_tile_png(), media_type="image/png")

    try:
        warp_opts = gdal.WarpOptions(
            format="MEM",
            width=256,
            height=256,
            outputBounds=[lon_min, lat_min, lon_max, lat_max],
            resampleAlg="bilinear"
        )
        tile_ds = gdal.Warp("", ds, options=warp_opts)
        if not tile_ds:
            return Response(content=get_transparent_tile_png(), media_type="image/png")

        band = tile_ds.GetRasterBand(1)
        data = band.ReadAsArray()
        tile_ds = None

        rgba = np.zeros((256, 256, 4), dtype=np.uint8)
        mask = data > 0
        rgba[mask, 0] = data[mask]
        rgba[mask, 1] = data[mask]
        rgba[mask, 2] = data[mask]
        rgba[mask, 3] = 255

        img = Image.fromarray(rgba)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()

        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            with open(cache_file, "wb") as f:
                f.write(png_bytes)
        except Exception:
            pass

        return Response(content=png_bytes, media_type="image/png", headers={"Cache-Control": "public, max-age=86400", "X-Tile-Cache": "MISS"})
    except Exception:
        return Response(content=get_transparent_tile_png(), media_type="image/png")


@router.get("/hirise/{z}/{x}/{y}.png", summary="Local Jezero HiRISE High-Res Tile (0.5 m/px)")
async def get_hirise_tile(
    z: int,
    x: int,
    y: int,
    scheme: str = Query("geographic", description="Tiling scheme"),
    science_access: ZuhuraScienceAccess = Depends(get_science_access)
):
    """
    Renders sub-meter high-resolution surface detail over Perseverance touchdown & delta from MRO HiRISE.
    Returns transparent PNG outside HiRISE coverage.
    """
    if z < 0 or z > 18:
        return Response(content=get_transparent_tile_png(), media_type="image/png")
    lon_min, lat_min, lon_max, lat_max = compute_tile_bounds(z, x, y, scheme=scheme)

    # Footprint overlap check [77.5158, 18.2876, 77.6537, 18.5834]
    if lon_max < 77.5158 or lon_min > 77.6537 or lat_max < 18.2876 or lat_min > 18.5834:
        return Response(content=get_transparent_tile_png(), media_type="image/png")

    cache_dir = Path(settings.TILES_CACHE_DIR) / "hirise" / str(z) / str(x)
    cache_file = cache_dir / f"{y}.png"
    if cache_file.exists():
        with open(cache_file, "rb") as f:
            return Response(content=f.read(), media_type="image/png", headers={"Cache-Control": "public, max-age=86400", "X-Tile-Cache": "HIT"})

    ds = get_hirise_ds(science_access.repo_root)
    if not ds:
        return Response(content=get_transparent_tile_png(), media_type="image/png")

    try:
        warp_opts = gdal.WarpOptions(
            format="MEM",
            width=256,
            height=256,
            outputBounds=[lon_min, lat_min, lon_max, lat_max],
            resampleAlg="bilinear"
        )
        tile_ds = gdal.Warp("", ds, options=warp_opts)
        if not tile_ds:
            return Response(content=get_transparent_tile_png(), media_type="image/png")

        arr = tile_ds.ReadAsArray()
        tile_ds = None

        if arr.ndim == 3 and arr.shape[0] >= 3:
            r, g, b = arr[0], arr[1], arr[2]
            mask = (r > 0) | (g > 0) | (b > 0)
            rgba = np.zeros((256, 256, 4), dtype=np.uint8)
            rgba[mask, 0] = r[mask]
            rgba[mask, 1] = g[mask]
            rgba[mask, 2] = b[mask]
            rgba[mask, 3] = 255
        else:
            return Response(content=get_transparent_tile_png(), media_type="image/png")

        img = Image.fromarray(rgba)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()

        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            with open(cache_file, "wb") as f:
                f.write(png_bytes)
        except Exception:
            pass

        return Response(content=png_bytes, media_type="image/png", headers={"Cache-Control": "public, max-age=86400", "X-Tile-Cache": "MISS"})
    except Exception:
        return Response(content=get_transparent_tile_png(), media_type="image/png")


@router.get("/cog/{z}/{x}/{y}.png", summary="Dynamic MOLA Global COG XYZ Tile")
@router.get("/{product_id}/{z}/{x}/{y}.png", summary="Dynamic Scientific Raster XYZ Tile")
async def get_tile(
    z: int,
    x: int,
    y: int,
    product_id: Optional[str] = "mola_global_meg128_cog",
    colormap: str = Query("terrain", description="Scientific colormap: terrain, viridis, plasma, inferno, gray"),
    scheme: str = Query("geographic", description="Tiling scheme: geographic (Cesium default) or webmercator"),
    min_elev: float = Query(-8200.0, description="Minimum elevation for color ramp"),
    max_elev: float = Query(21200.0, description="Maximum elevation for color ramp"),
    science_access: ZuhuraScienceAccess = Depends(get_science_access)
):
    """
    Renders an on-the-fly 256x256 PNG map tile directly from the Cloud-Optimized GeoTIFF overview pyramids.
    Applies high-speed disk caching and NoData transparency.
    """
    # 1. Resolve product file
    if product_id in ["cog", "mola", "default", "mola_global_meg128_cog"]:
        raster_path = science_access.mola_cog_path
        is_elevation = True
    else:
        prod = science_access.get_product(product_id)
        if not prod or not prod.storage_path:
            raise HTTPException(status_code=404, detail=f"Raster product '{product_id}' not found.")
        raster_path = science_access.repo_root / prod.storage_path
        is_elevation = (prod.product_type.value == "raster_elevation")

    if not raster_path.exists():
        raise HTTPException(status_code=404, detail="Raster file asset missing on disk.")

    # 2. Check disk cache
    cache_dir = Path(settings.TILES_CACHE_DIR) / f"{product_id}_{colormap}_{scheme}" / str(z) / str(x)
    cache_file = cache_dir / f"{y}.png"
    if cache_file.exists():
        with open(cache_file, "rb") as f:
            return Response(
                content=f.read(),
                media_type="image/png",
                headers={"Cache-Control": "public, max-age=86400", "X-Tile-Cache": "HIT"}
            )

    # 3. Compute geographic bounding box
    lon_min, lat_min, lon_max, lat_max = compute_tile_bounds(z, x, y, scheme=scheme)

    # Check bounds overlap with Mars global coverage
    if lat_max < -88.0 or lat_min > 88.0:
        # Completely out of MOLA global range: return transparent tile
        empty_img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        buf = io.BytesIO()
        empty_img.save(buf, format="PNG")
        return Response(content=buf.getvalue(), media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})

    # 4. Project bounding box to Mars_simpCyl_c180:
    # x = R * (lon - 180) * pi / 180
    # y = R * lat * pi / 180
    # Normalize longitude to East-positive [0, 360)
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
    p_ymin = min(to_mola_y(lat_min), to_mola_y(lat_max))
    p_ymax = max(to_mola_y(lat_min), to_mola_y(lat_max))

    try:
        warp_opts = gdal.WarpOptions(
            format="MEM",
            width=256,
            height=256,
            outputBounds=[p_xmin, p_ymin, p_xmax, p_ymax],
            resampleAlg="bilinear"
        )
        ds_tile = gdal.Warp("", str(raster_path), options=warp_opts)
        if not ds_tile:
            raise RuntimeError("GDAL Warp failed to produce tile.")

        band1 = ds_tile.GetRasterBand(1)
        arr = band1.ReadAsArray()
        ds_tile = None
    except Exception as e:
        # Return fallback transparent tile
        empty_img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        buf = io.BytesIO()
        empty_img.save(buf, format="PNG")
        return Response(content=buf.getvalue(), media_type="image/png")

    # 5. Apply Scientific Colormap or Grayscale stretch
    if is_elevation:
        # Scale between min_elev and max_elev
        norm = np.clip((arr.astype(np.float32) - min_elev) / (max_elev - min_elev), 0.0, 1.0)
        try:
            cmap = matplotlib.colormaps.get(colormap, matplotlib.colormaps["terrain"])
        except Exception:
            cmap = matplotlib.colormaps["terrain"]
        rgba = (cmap(norm) * 255).astype(np.uint8)
        
        # Transparent outside MOLA bounds or if nodata
        mask_transparent = (arr == -99999) | (arr == 0) & (arr.min() == arr.max() and arr[0,0] == 0)
        rgba[mask_transparent, 3] = 0
    else:
        # Grayscale / 8-bit imagery
        if arr.ndim == 2:
            norm = np.clip(arr.astype(np.float32) / 255.0, 0.0, 1.0)
            rgba = np.stack([norm * 255, norm * 255, norm * 255, np.full_like(norm, 255)], axis=-1).astype(np.uint8)
        else:
            rgba = arr

    # 6. Encode PNG
    img = Image.fromarray(rgba)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    # 7. Write to disk cache
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "wb") as f:
            f.write(png_bytes)
    except Exception:
        pass

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400", "X-Tile-Cache": "MISS"}
    )





@router.get("/terrain/jezero/layer.json", summary="Cesium Quantized-Mesh Terrain Layer Metadata (Jezero)")
@router.get("/terrain/{region}/layer.json", summary="Cesium Quantized-Mesh Terrain Layer Metadata")
async def get_terrain_layer_json(region: str = "jezero"):
    """Returns layer.json metadata for global or regional Quantized-Mesh 1.0 terrain."""
    if ".." in region or "/" in region:
        raise HTTPException(status_code=400, detail="Invalid region parameter.")
    layer_file = Path(settings.DATA_REPO_ROOT) / f"data/tiles/terrain/{region}/layer.json"
    if not layer_file.exists():
        raise HTTPException(status_code=404, detail=f"Terrain layer.json for '{region}' not found.")
    with open(layer_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # For regional models, ensure contiguous availability array from level 0 to maxzoom
    # so Cesium does not prematurely clamp the maximum terrain zoom level to 1.
    if region != "global" and "metadata" in meta and "tile_coords" in meta["metadata"]:
        coords = meta["metadata"]["tile_coords"]
        zoom = coords.get("z", meta.get("maxzoom", 0))
        x_tile = coords.get("x", 0)
        y_tms = coords.get("y_tms", 0)

        avail = []
        for z in range(zoom + 1):
            shift = zoom - z
            xz = x_tile >> shift
            yz = y_tms >> shift
            avail.append([{"startX": xz, "endX": xz, "startY": yz, "endY": yz}])
        # Level 0 covers both Mars hemisphere tiles
        avail[0] = [{"startX": 0, "endX": 1, "startY": 0, "endY": 0}]
        meta["available"] = avail

    return meta


@router.get("/terrain/jezero/{z}/{x}/{y}.terrain", summary="Cesium Quantized-Mesh 1.0 Binary Terrain Tile (Jezero)")
@router.get("/terrain/{region}/{z}/{x}/{y}.terrain", summary="Cesium Quantized-Mesh 1.0 Binary Terrain Tile")
async def get_terrain_tile(z: int, x: int, y: int, region: str = "jezero"):
    """Serves Quantized-Mesh 1.0 binary terrain tile for global or regional terrain."""
    if ".." in region or "/" in region:
        raise HTTPException(status_code=400, detail="Invalid region parameter.")
    terrain_file = Path(settings.DATA_REPO_ROOT) / f"data/tiles/terrain/{region}/{z}/{x}/{y}.terrain"
    if not terrain_file.exists():
        # Fallback to global terrain base pyramid for smooth planetary multi-resolution coverage
        global_file = Path(settings.DATA_REPO_ROOT) / f"data/tiles/terrain/global/{z}/{x}/{y}.terrain"
        if global_file.exists():
            terrain_file = global_file
        else:
            raise HTTPException(status_code=404, detail=f"Terrain tile {region}/{z}/{x}/{y}.terrain not found.")

    with open(terrain_file, "rb") as f:
        tile_data = f.read()

    return Response(
        content=tile_data,
        media_type="application/vnd.quantized-mesh",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Content-Type": "application/vnd.quantized-mesh"
        }
    )


@router.get("/trek/{layer_label}/{z}/{x}/{y}.jpg", summary="Mars Trek WMTS Cached Proxy Tile (JPEG)")
@router.get("/trek/{layer_label}/{z}/{x}/{y}.png", summary="Mars Trek WMTS Cached Proxy Tile (PNG)")
async def get_trek_tile(layer_label: str, z: int, x: int, y: int):
    """
    Proxies and caches authentic NASA Mars Trek WMTS tiles with disk caching.
    Ensures zero CORS errors, fast repeat access, and graceful fallback for out-of-bounds tiles.
    """
    import urllib.request
    safe_label = Path(layer_label).name
    cache_path = Path(settings.TILES_CACHE_DIR) / "trek" / safe_label / str(z) / str(x) / f"{y}.jpg"
    if cache_path.exists():
        with open(cache_path, "rb") as f:
            return Response(
                content=f.read(),
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=86400"}
            )

    remote_url = f"https://trek.nasa.gov/tiles/Mars/EQ/{safe_label}/1.0.0/default/default028mm/{z}/{y}/{x}.jpg"
    try:
        req = urllib.request.Request(remote_url, headers={"User-Agent": "ZuhuraMarsTileProxy/2.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = resp.read()
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "wb") as f:
                f.write(data)
            return Response(
                content=data,
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=86400"}
            )
    except Exception:
        # Return transparent tile on 404 or boundary limit
        return Response(
            content=get_transparent_tile_png(),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"}
        )

