"""
Pydantic schemas for terrain analysis.
Strict Pydantic v2 schemas validating spatial coordinate conventions,
raster window parameters, and scientific terrain derivative payloads.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class Coordinate(BaseModel):
    """
    Planetary coordinate representation enforcing planetocentric latitude
    and east-positive longitude conventions on Mars.
    """
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Planetocentric latitude in degrees (-90 to +90)")
    longitude: float = Field(..., description="East-positive longitude in degrees (-180 to 360)")

    @field_validator("longitude")
    @classmethod
    def normalize_longitude(cls, v: float) -> float:
        norm = v % 360.0
        return round(norm if norm >= 0.0 else norm + 360.0, 6)


class PointAnalysisRequest(BaseModel):
    """Request payload for instantaneous terrain derivative calculation at a point."""
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Planetocentric latitude in degrees")
    longitude: float = Field(..., description="East-positive longitude in degrees")
    include_morphometry: bool = Field(default=True, description="Whether to include TRI, TPI and local relief")
    kernel_size: int = Field(default=3, description="Kernel window size: 3, 5, or 7")

    @field_validator("longitude")
    @classmethod
    def normalize_lon(cls, v: float) -> float:
        norm = v % 360.0
        return round(norm if norm >= 0.0 else norm + 360.0, 6)

    @field_validator("kernel_size")
    @classmethod
    def validate_kernel(cls, v: int) -> int:
        if v not in [3, 5, 7]:
            raise ValueError("kernel_size must be 3, 5, or 7")
        return v


class PointAnalysisResponse(BaseModel):
    """Scientific terrain analysis response for a single surface coordinate."""
    coordinate: Dict[str, Any]
    elevation: Dict[str, Any]
    derivatives: Dict[str, Any]
    morphometry: Optional[Dict[str, Any]] = None
    provenance: Dict[str, Any]


class TerrainProfileRequest(BaseModel):
    """Request payload for great-circle geodesic transect extraction."""
    start_point: Coordinate
    end_point: Coordinate
    num_samples: int = Field(default=50, ge=5, le=500, description="Number of profile sample stations (5 to 500)")
    include_derivatives: bool = Field(default=True, description="Whether to calculate segment slopes")
    interpolation_method: Literal["bilinear", "nearest"] = Field(
        default="bilinear",
        description="Sub-pixel raster sampling method"
    )


class TerrainProfileResponse(BaseModel):
    """Geodesic transect profile with summary statistics and station samples."""
    transect_summary: Dict[str, Any]
    samples: List[Dict[str, Any]]
    provenance: Dict[str, Any]


class TerrainStatisticsRequest(BaseModel):
    """Request payload for focal morphometric statistics across a circular footprint."""
    center_point: Coordinate
    radius_km: float = Field(..., gt=0.1, le=250.0, description="Sampling circle radius in kilometers (0.1 to 250 km)")


class TerrainStatisticsResponse(BaseModel):
    """Morphometric distributions across a circular geographic footprint."""
    query_region: Dict[str, Any]
    elevation_statistics: Dict[str, Any]
    slope_statistics: Dict[str, Any]
    roughness_indices: Dict[str, Any]
    provenance: Dict[str, Any]


class TerrainCompareRequest(BaseModel):
    """Request payload comparing two candidate surface landing/investigation sites."""
    site_a: Coordinate
    site_b: Coordinate
    name_a: Optional[str] = Field(default="Site A", description="Descriptive label for site A")
    name_b: Optional[str] = Field(default="Site B", description="Descriptive label for site B")


class TerrainCompareResponse(BaseModel):
    """Comparative morphometry, elevation delta, and separation distance between two sites."""
    separation: Dict[str, Any]
    comparison_matrix: Dict[str, Any]
    provenance: Dict[str, Any]
