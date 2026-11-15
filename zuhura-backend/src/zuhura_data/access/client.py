"""
Zuhura Planetary Digital Twin - Scientific Query & Data Access Client
Provides Python interfaces for searching datasets, inspecting metadata,
performing coordinate elevation queries from MOLA COG, and streaming raster windows.
Designed to be directly consumed by the FastAPI backend (zuhura-backend).
"""

import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
try:
    from osgeo import gdal, osr
except ImportError:
    gdal = None  # type: ignore
    osr = None  # type: ignore

from zuhura_data.catalog.manager import CatalogManager
from zuhura_data.models.catalog import ScientificCatalog
from zuhura_data.models.scientific_product import (
    DatasetFamily,
    ProductLevel,
    ProductType,
    ScientificProduct
)
from zuhura_data.models.spatial import (
    BoundingBox,
    SpatialCoverage,
    normalize_longitude_360
)
from zuhura_data.models.provenance import ValidationStatus

# Mars IAU Spherical Model for MOLA Simple Cylindrical
MOLA_SPHERE_RADIUS_M = 3396000.0


class ZuhuraScienceAccess:
    """
    Primary scientific data access client for Zuhura backend integration.
    """
    def __init__(
        self,
        catalog_path: Optional[Path] = None,
        repo_root: Optional[Path] = None
    ):
        self.repo_root = repo_root or Path("/home/anonymous/Zuhura/zuhura-data")
        default_cat_path = self.repo_root / "catalogs/zuhura_science_catalog.json"
        self.catalog_path = catalog_path or default_cat_path
        
        if self.catalog_path.exists():
            self.manager = CatalogManager.load_from_file(self.catalog_path)
        else:
            self.manager = CatalogManager()

        # Path to MOLA Global COG
        self.mola_cog_path = self.repo_root / "data/processed/mola/global_v3/mola_global_meg128_cog.tif"

    def list_datasets(
        self,
        family: Optional[DatasetFamily] = None,
        instrument: Optional[str] = None,
        product_level: Optional[ProductLevel] = None,
        validation_status: Optional[ValidationStatus] = None
    ) -> List[ScientificProduct]:
        """List all indexed datasets matching optional criteria."""
        return self.manager.search(
            family=family,
            instrument=instrument,
            product_level=product_level,
            validation_status=validation_status
        )

    def get_product(self, identifier: str) -> Optional[ScientificProduct]:
        """Retrieve full scientific metadata for a specific dataset or archive product."""
        return self.manager.get_product(identifier)

    def search_by_area(
        self,
        min_lon: float,
        max_lon: float,
        min_lat: float,
        max_lat: float,
        family: Optional[DatasetFamily] = None,
        instrument: Optional[str] = None,
        product_level: Optional[ProductLevel] = None
    ) -> List[ScientificProduct]:
        """Find observations intersecting a geographic bounding box."""
        bbox = BoundingBox(
            min_lon=min_lon,
            max_lon=max_lon,
            min_lat=min_lat,
            max_lat=max_lat
        )
        return self.manager.search(
            bbox=bbox,
            family=family,
            instrument=instrument,
            product_level=product_level
        )

    def search_by_time(
        self,
        time_start: datetime,
        time_end: datetime,
        family: Optional[DatasetFamily] = None,
        instrument: Optional[str] = None
    ) -> List[ScientificProduct]:
        """Find observations acquired within a specified time interval."""
        return self.manager.search(
            time_start=time_start,
            time_end=time_end,
            family=family,
            instrument=instrument
        )

    def search_by_point(
        self,
        lat: float,
        lon: float,
        family: Optional[DatasetFamily] = None
    ) -> List[ScientificProduct]:
        """Find all observation footprints covering a specific Mars coordinate."""
        return self.manager.search(
            point=(lat, lon),
            family=family
        )

    def get_elevation_at_point(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Query MOLA global elevation COG at a specific Mars coordinate (lat, lon).
        Uses GDAL single-pixel window read without loading the 961 MB raster.
        """
        norm_lon = normalize_longitude_360(lon)
        if not (-88.0 <= lat <= 88.0):
            return {
                "latitude": lat,
                "longitude": norm_lon,
                "elevation_m": None,
                "nodata_status": True,
                "error": "Latitude outside global MOLA coverage boundary (-88 to +88)"
            }

        if gdal is None or not self.mola_cog_path.exists():
            return {
                "latitude": lat,
                "longitude": norm_lon,
                "elevation_m": 0.0,
                "source_product_id": "mola_global_meg128_cog",
                "nodata_status": True,
                "error": "Dataset raster not present on cloud deployment",
                "query_timestamp": datetime.now(timezone.utc).isoformat()
            }

        ds = gdal.Open(str(self.mola_cog_path))
        gt = ds.GetGeoTransform()

        # Project (lon, lat) to Mars_simpCyl_c180:
        # simpCyl centered at 180° East:
        # x = R * (lon - 180) * (pi / 180)
        # y = R * lat * (pi / 180)
        lat_rad = math.radians(lat)
        lon_diff_rad = math.radians(norm_lon - 180.0)
        x_proj = MOLA_SPHERE_RADIUS_M * lon_diff_rad
        y_proj = MOLA_SPHERE_RADIUS_M * lat_rad

        # Compute pixel offsets
        px = int((x_proj - gt[0]) / gt[1])
        py = int((y_proj - gt[3]) / gt[5])

        # Clamp check
        if px < 0 or px >= ds.RasterXSize or py < 0 or py >= ds.RasterYSize:
            return {
                "latitude": lat,
                "longitude": norm_lon,
                "elevation_m": None,
                "nodata_status": True,
                "error": "Projected coordinate falls outside raster bounds"
            }

        band = ds.GetRasterBand(1)
        data = band.ReadAsArray(px, py, 1, 1)
        elev = int(data[0, 0])
        ds = None

        return {
            "latitude": lat,
            "longitude": norm_lon,
            "elevation_m": elev,
            "source_product_id": "mola_global_meg128_cog",
            "pixel_coordinates": {"x": px, "y": py},
            "native_crs": "Mars_simpCyl_c180 (IAU:49900 Sphere R=3396km, Central Meridian 180E)",
            "vertical_datum": "MOLA GMM-3 Areoid (Equipotential Reference Surface)",
            "nodata_status": False,
            "query_timestamp": datetime.now(timezone.utc).isoformat()
        }

    def get_elevation_window(
        self,
        lat: float,
        lon: float,
        half_window: int = 1
    ) -> Dict[str, Any]:
        """
        Query MOLA global elevation COG extracting a (2*half_window + 1) square window
        centered at (lat, lon) with seamless antimeridian (0°/360°E) wrapping and
        latitude-dependent metric cell dimensions.
        """
        norm_lon = normalize_longitude_360(lon)
        if not (-88.0 <= lat <= 88.0):
            # Route to polar DEM if available
            return self.get_polar_elevation_at_point(lat, norm_lon)

        if gdal is None or not self.mola_cog_path.exists():
            w_size = 2 * half_window + 1
            return np.zeros((w_size, w_size), dtype=np.float32)

        ds = gdal.Open(str(self.mola_cog_path))
        band = ds.GetRasterBand(1)
        gt = ds.GetGeoTransform()

        lat_rad = math.radians(lat)
        lon_diff_rad = math.radians(norm_lon - 180.0)
        x_proj = MOLA_SPHERE_RADIUS_M * lon_diff_rad
        y_proj = MOLA_SPHERE_RADIUS_M * lat_rad

        fx = (x_proj - gt[0]) / gt[1]
        fy = (y_proj - gt[3]) / gt[5]
        px = int(round(fx))
        py = int(round(fy))

        w_size = 2 * half_window + 1
        wx_total = ds.RasterXSize
        px_start = px - half_window
        px_end = px + half_window + 1
        py_start = py - half_window
        py_end = py + half_window + 1

        y_read_start = max(0, py_start)
        y_read_end = min(ds.RasterYSize, py_end)
        read_h = y_read_end - y_read_start

        if 0 <= px_start and px_end <= wx_total:
            arr = band.ReadAsArray(px_start, y_read_start, w_size, read_h)
        elif px_start < 0:
            w_left = -px_start
            left_arr = band.ReadAsArray(wx_total - w_left, y_read_start, w_left, read_h)
            right_arr = band.ReadAsArray(0, y_read_start, px_end, read_h)
            arr = np.hstack([left_arr, right_arr])
        else:
            w_right = px_end - wx_total
            left_arr = band.ReadAsArray(px_start, y_read_start, wx_total - px_start, read_h)
            right_arr = band.ReadAsArray(0, y_read_start, w_right, read_h)
            arr = np.hstack([left_arr, right_arr])

        pad_top = y_read_start - py_start
        pad_bottom = py_end - y_read_end
        if pad_top > 0 or pad_bottom > 0:
            arr = np.pad(arr, ((pad_top, pad_bottom), (0, 0)), mode="edge")

        arr_float = arr.astype(np.float64)
        center_val = float(arr_float[half_window, half_window])

        # Latitude-scaled metric dimensions
        dx_m = abs(gt[1]) * math.cos(lat_rad)
        dy_m = abs(gt[5])
        ds = None

        return {
            "latitude": lat,
            "longitude": norm_lon,
            "elevation_m": center_val,
            "window": arr_float,
            "center_pixel": {"x": px, "y": py},
            "half_window": half_window,
            "metric_cell_size_m": {"dx_m": round(dx_m, 2), "dy_m": round(dy_m, 2)},
            "source_product_id": "mola_global_meg128_cog",
            "native_crs": "Mars_simpCyl_c180 (IAU:49900 Sphere R=3396km, Central Meridian 180E)",
            "vertical_datum": "MOLA GMM-3 Areoid (Equipotential Reference Surface)",
            "nodata_status": False,
            "query_timestamp": datetime.now(timezone.utc).isoformat()
        }

    def get_polar_elevation_at_point(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Query MOLA Polar Stereographic DEM for high-latitude observations (|lat| > 88.0°).
        """
        norm_lon = normalize_longitude_360(lon)
        is_north = lat >= 0.0
        polar_path = self.repo_root / (
            "data/processed/mola/polar_v2/megt_n_128_1.tif" if is_north
            else "data/processed/mola/polar_v2/megt_s_128_1.tif"
        )
        if not polar_path.exists():
            return {
                "latitude": lat,
                "longitude": norm_lon,
                "elevation_m": None,
                "nodata_status": True,
                "error": f"Polar DEM not found at: {polar_path}"
            }

        ds = gdal.Open(str(polar_path))
        gt = ds.GetGeoTransform()
        srs = osr.SpatialReference()
        srs.ImportFromWkt(ds.GetProjection())

        geo_srs = osr.SpatialReference()
        geo_srs.ImportFromProj4("+proj=longlat +R=3376200 +no_defs")
        ct = osr.CoordinateTransformation(geo_srs, srs)

        x_proj, y_proj, _ = ct.TransformPoint(norm_lon, lat)
        px = int((x_proj - gt[0]) / gt[1])
        py = int((y_proj - gt[3]) / gt[5])

        if px < 0 or px >= ds.RasterXSize or py < 0 or py >= ds.RasterYSize:
            ds = None
            return {
                "latitude": lat,
                "longitude": norm_lon,
                "elevation_m": None,
                "nodata_status": True,
                "error": "Coordinates outside polar raster bounding box"
            }

        band = ds.GetRasterBand(1)
        data = band.ReadAsArray(px, py, 1, 1)
        val = float(data[0, 0])
        nodata = band.GetNoDataValue()
        ds = None

        if nodata is not None and math.isclose(val, nodata, abs_tol=1e-3):
            return {
                "latitude": lat,
                "longitude": norm_lon,
                "elevation_m": None,
                "nodata_status": True,
                "error": "Polar DEM NoData value encountered"
            }

        return {
            "latitude": lat,
            "longitude": norm_lon,
            "elevation_m": round(val, 1),
            "source_product_id": "megt_n_128_1" if is_north else "megt_s_128_1",
            "pixel_coordinates": {"x": px, "y": py},
            "native_crs": "MarsNP_3376" if is_north else "MarsSP_3376",
            "vertical_datum": "MOLA GMM-3 Areoid (Equipotential Reference Surface)",
            "nodata_status": False,
            "query_timestamp": datetime.now(timezone.utc).isoformat()
        }

    def sample_transect_bilinear(
        self,
        coords: List[Tuple[float, float]]
    ) -> List[float]:
        """
        Sub-pixel bilinear elevation sampling along a sequence of (lat, lon) coordinates
        from MOLA Global COG. Reuses a single GDAL dataset handle for high performance.
        """
        if gdal is None or not self.mola_cog_path.exists():
            return [0.0] * len(coords)

        ds = gdal.Open(str(self.mola_cog_path))
        band = ds.GetRasterBand(1)
        gt = ds.GetGeoTransform()
        wx_total = ds.RasterXSize
        wy_total = ds.RasterYSize

        elevations: List[float] = []

        for lat, lon in coords:
            norm_lon = normalize_longitude_360(lon)
            if not (-88.0 <= lat <= 88.0):
                # Fallback to polar point lookup
                polar_res = self.get_polar_elevation_at_point(lat, norm_lon)
                elevations.append(polar_res.get("elevation_m") or 0.0)
                continue

            lat_rad = math.radians(lat)
            lon_diff_rad = math.radians(norm_lon - 180.0)
            x_proj = MOLA_SPHERE_RADIUS_M * lon_diff_rad
            y_proj = MOLA_SPHERE_RADIUS_M * lat_rad

            fx = (x_proj - gt[0]) / gt[1]
            fy = (y_proj - gt[3]) / gt[5]

            x0 = int(math.floor(fx))
            y0 = int(math.floor(fy))
            wx = fx - x0
            wy = fy - y0

            y0 = max(0, min(wy_total - 2, y0))
            y1 = y0 + 1

            if 0 <= x0 < wx_total - 1:
                w2 = band.ReadAsArray(x0, y0, 2, 2).astype(np.float64)
                z00, z10 = w2[0, 0], w2[0, 1]
                z01, z11 = w2[1, 0], w2[1, 1]
            else:
                rx0 = x0 % wx_total
                rx1 = (x0 + 1) % wx_total
                c0 = band.ReadAsArray(rx0, y0, 1, 2).astype(np.float64)
                c1 = band.ReadAsArray(rx1, y0, 1, 2).astype(np.float64)
                z00, z01 = c0[0, 0], c0[1, 0]
                z10, z11 = c1[0, 0], c1[1, 0]

            # Bilinear interpolation equation
            z_interp = (
                (1.0 - wx) * (1.0 - wy) * z00 +
                wx * (1.0 - wy) * z10 +
                (1.0 - wx) * wy * z01 +
                wx * wy * z11
            )
            elevations.append(round(float(z_interp), 2))

        ds = None
        return elevations

    def read_raster_window(
        self,
        product_id: str,
        col_offset: int,
        row_offset: int,
        width: int,
        height: int,
        band_index: int = 1
    ) -> np.ndarray:
        """
        Read a localized sub-window array from any validated raster or spectral product.
        """
        prod = self.get_product(product_id)
        if not prod or not prod.storage_path:
            raise ValueError(f"Product '{product_id}' has no local storage path configured.")

        full_path = self.repo_root / prod.storage_path
        if not full_path.exists():
            raise FileNotFoundError(f"Raster file not found on disk: {full_path}")

        ds = gdal.Open(str(full_path))
        if not ds:
            raise RuntimeError(f"GDAL failed to open raster: {full_path}")

        band = ds.GetRasterBand(band_index)
        arr = band.ReadAsArray(col_offset, row_offset, width, height)
        ds = None
        return arr

    def get_raster_info(self, product_id: str) -> Dict[str, Any]:
        """Retrieve detailed GDAL header and overview information for a raster."""
        prod = self.get_product(product_id)
        if not prod or not prod.storage_path:
            raise ValueError(f"Product '{product_id}' has no local storage path.")

        full_path = self.repo_root / prod.storage_path
        ds = gdal.Open(str(full_path))
        if not ds:
            raise RuntimeError(f"GDAL failed to open raster: {full_path}")

        band = ds.GetRasterBand(1)
        info = {
            "dataset_id": prod.dataset_id,
            "product_id": prod.product_id,
            "file_path": str(full_path),
            "driver": ds.GetDriver().ShortName,
            "dimensions": [ds.RasterXSize, ds.RasterYSize, ds.RasterCount],
            "data_type": gdal.GetDataTypeName(band.DataType),
            "nodata_value": band.GetNoDataValue(),
            "geotransform": list(ds.GetGeoTransform()),
            "projection_wkt": ds.GetProjection(),
            "overview_count": band.GetOverviewCount(),
            "overviews": [
                [band.GetOverview(i).XSize, band.GetOverview(i).YSize]
                for i in range(band.GetOverviewCount())
            ]
        }
        ds = None
        return info
