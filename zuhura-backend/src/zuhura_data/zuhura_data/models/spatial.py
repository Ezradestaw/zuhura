"""
Zuhura Planetary Digital Twin - Spatial Geometry & Mars Coordinates Model
Handles Mars ellipsoidal coordinates, bounding boxes, polygon footprints,
and longitude wrapping across prime meridian and antimeridian.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, model_validator
from osgeo import ogr, osr


class CoordinateConvention(str, Enum):
    PLANETOCENTRIC = "planetocentric"
    PLANETOGRAPHIC = "planetographic"


class LongitudeConvention(str, Enum):
    EAST_POSITIVE = "east_positive"
    WEST_POSITIVE = "west_positive"


def normalize_longitude_360(lon: float) -> float:
    """Normalize longitude to [0, 360) East-positive."""
    normalized = lon % 360.0
    if normalized < 0:
        normalized += 360.0
    return normalized


def normalize_longitude_180(lon: float) -> float:
    """Normalize longitude to [-180, 180) East-positive."""
    lon360 = normalize_longitude_360(lon)
    if lon360 > 180.0:
        return lon360 - 360.0
    return lon360


class BoundingBox(BaseModel):
    """
    Geographic bounding envelope on Mars.
    """
    min_lon: float = Field(..., description="Western boundary in degrees")
    max_lon: float = Field(..., description="Eastern boundary in degrees")
    min_lat: float = Field(..., ge=-90.0, le=90.0, description="Southern boundary in degrees")
    max_lat: float = Field(..., ge=-90.0, le=90.0, description="Northern boundary in degrees")
    longitude_convention: LongitudeConvention = LongitudeConvention.EAST_POSITIVE
    latitude_convention: CoordinateConvention = CoordinateConvention.PLANETOCENTRIC

    @model_validator(mode="after")
    def validate_latitude_order(self) -> "BoundingBox":
        if self.min_lat > self.max_lat:
            raise ValueError(f"min_lat ({self.min_lat}) cannot exceed max_lat ({self.max_lat})")
        return self

    @property
    def crosses_prime_meridian(self) -> bool:
        """True if box crosses 0°/360° boundary in [0, 360) space."""
        return self.min_lon > self.max_lon

    def to_wkt(self) -> str:
        """Export box as WKT POLYGON (or MULTIPOLYGON if wrapping)."""
        if not self.crosses_prime_meridian:
            return (
                f"POLYGON (({self.min_lon} {self.min_lat}, {self.max_lon} {self.min_lat}, "
                f"{self.max_lon} {self.max_lat}, {self.min_lon} {self.max_lat}, {self.min_lon} {self.min_lat}))"
            )
        # Split into two polygons across 0/360
        poly1 = (
            f"(({self.min_lon} {self.min_lat}, 360.0 {self.min_lat}, "
            f"360.0 {self.max_lat}, {self.min_lon} {self.max_lat}, {self.min_lon} {self.min_lat}))"
        )
        poly2 = (
            f"((0.0 {self.min_lat}, {self.max_lon} {self.min_lat}, "
            f"{self.max_lon} {self.max_lat}, 0.0 {self.max_lat}, 0.0 {self.min_lat}))"
        )
        return f"MULTIPOLYGON ({poly1}, {poly2})"

    def contains_point(self, lat: float, lon: float) -> bool:
        """Test if Mars point (lat, lon) is contained in this box."""
        if not (self.min_lat <= lat <= self.max_lat):
            return False
        norm_lon = normalize_longitude_360(lon)
        if not self.crosses_prime_meridian:
            return self.min_lon <= norm_lon <= self.max_lon
        else:
            return (norm_lon >= self.min_lon) or (norm_lon <= self.max_lon)


class SpatialCoverage(BaseModel):
    """
    Spatial coverage representation combining bounding box, footprint geometry,
    and OGR-powered intersection operations.
    """
    bbox: BoundingBox
    geometry_wkt: Optional[str] = None
    geojson: Optional[Dict[str, Any]] = None
    center_lat: Optional[float] = None
    center_lon: Optional[float] = None

    def get_ogr_geometry(self) -> ogr.Geometry:
        """Return OGR geometry object for spatial analysis."""
        if self.geometry_wkt:
            geom = ogr.CreateGeometryFromWkt(self.geometry_wkt)
            if geom:
                return geom
        # Fall back to bounding box polygon
        return ogr.CreateGeometryFromWkt(self.bbox.to_wkt())

    def intersects(self, other_coverage: "SpatialCoverage") -> bool:
        """Evaluate exact spatial intersection with another spatial coverage."""
        g1 = self.get_ogr_geometry()
        g2 = other_coverage.get_ogr_geometry()
        if not g1 or not g2:
            return False
        return bool(g1.Intersects(g2))

    def intersection_area_deg2(self, other_coverage: "SpatialCoverage") -> float:
        """Compute intersection area in square degrees."""
        g1 = self.get_ogr_geometry()
        g2 = other_coverage.get_ogr_geometry()
        if not g1 or not g2:
            return 0.0
        inter = g1.Intersection(g2)
        if inter is None or inter.IsEmpty():
            return 0.0
        return float(inter.GetArea())

    def contains_point(self, lat: float, lon: float) -> bool:
        """Check if point is inside coverage footprint."""
        pt = ogr.Geometry(ogr.wkbPoint)
        pt.AddPoint(normalize_longitude_360(lon), lat)
        geom = self.get_ogr_geometry()
        if geom and not geom.IsEmpty():
            return bool(geom.Contains(pt))
        return self.bbox.contains_point(lat, lon)
