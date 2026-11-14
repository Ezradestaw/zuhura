"""
Zuhura Planetary Digital Twin - Unified Scientific Product Model
Defines the canonical metadata representation for all Mars observations,
rasters, spectral cubes, in-situ measurements, and derived products.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from zuhura_data.models.spatial import SpatialCoverage
from zuhura_data.models.provenance import (
    FileProvenance,
    ProvenanceHistory,
    ValidationStatus
)


class DatasetFamily(str, Enum):
    MOLA = "mola"
    VIKING_MDIM = "viking_mdim"
    THEMIS = "themis"
    CTX = "ctx"
    HIRISE = "hirise"
    CRISM = "crism"
    OMEGA = "omega"
    MAVEN = "maven"
    MCS = "mcs"
    SHARAD = "sharad"
    MARSIS = "marsis"
    INSIGHT = "insight"
    ROVER = "rover"
    GRAVITY = "gravity"


class ProductType(str, Enum):
    RASTER_ELEVATION = "raster_elevation"
    RASTER_IMAGERY = "raster_imagery"
    SPECTRAL_CUBE = "spectral_cube"
    VECTOR_FOOTPRINT = "vector_footprint"
    POINT_CLOUD = "point_cloud"
    TIME_SERIES = "time_series"
    TABLE = "table"
    GEOLOGIC_MAP = "geologic_map"


class ProductLevel(str, Enum):
    RAW = "raw_observation"
    CALIBRATED = "calibrated"
    DERIVED = "derived_product"
    MAP_PROJECTED = "map_projected"
    MOSAIC = "mosaic"
    INTERPRETATION = "interpretation"
    SIMULATION = "simulation"


class TemporalCoverage(BaseModel):
    """Observation time interval."""
    start_time: datetime
    stop_time: Optional[datetime] = None
    solar_longitude_deg: Optional[float] = None
    martian_year: Optional[int] = None
    orbit_number: Optional[int] = None


class SpectralBandInfo(BaseModel):
    """Spectral band metadata."""
    band_number: int
    band_name: Optional[str] = None
    center_wavelength_um: float
    bandwidth_um: Optional[float] = None
    units: str


class SpectralInformation(BaseModel):
    """Multispectral / hyperspectral properties."""
    band_count: int
    spectral_range_um: Optional[str] = None
    bands: List[SpectralBandInfo] = Field(default_factory=list)


class CalibrationInfo(BaseModel):
    """Radiometric, photometric, or physical calibration metadata."""
    calibration_level: str
    formula: Optional[str] = None
    dark_current_corrected: Optional[bool] = None
    radiometrically_calibrated: Optional[bool] = None
    photometrically_corrected: Optional[bool] = None
    atmospheric_corrected: Optional[bool] = None
    thermal_model: Optional[str] = None
    calibration_notes: Optional[str] = None


class NoDataPolicy(BaseModel):
    """NoData and special value interpretation."""
    nodata_value: Optional[float] = None
    sentinel_values: Dict[str, float] = Field(default_factory=dict)
    datum_zero_is_valid: bool = False
    description: str


class ScientificProduct(BaseModel):
    """
    Canonical metadata representation for a Mars scientific observation in Zuhura.
    Strictly follows planetary geodetic standards and preserves native mission metadata.
    """
    dataset_id: str = Field(..., description="Stable internal identifier, e.g. zuhura-themis-ir-jezero")
    dataset_family: DatasetFamily = Field(..., description="Dataset family (MOLA, THEMIS, CTX, HiRISE, etc.)")
    mission: str = Field(..., description="Spacecraft / mission name (e.g. 2001 Mars Odyssey, MRO)")
    instrument: str = Field(..., description="Instrument acronym (e.g. THEMIS, CTX, HiRISE, MOLA)")
    product_id: str = Field(..., description="Original archive product identifier (e.g. I02413002RDR)")
    observation_id: Optional[str] = Field(None, description="Original observation identifier")
    product_type: ProductType = Field(..., description="Raster, vector, spectral cube, etc.")
    product_level: ProductLevel = Field(..., description="Raw, calibrated, derived, map-projected")
    
    acquisition_time: Optional[datetime] = Field(None, description="UTC acquisition timestamp")
    spatial_coverage: SpatialCoverage = Field(..., description="Geographic footprint & bounding box")
    temporal_coverage: Optional[TemporalCoverage] = Field(None, description="Time interval & solar longitude")
    
    native_crs: str = Field(..., description="Original coordinate reference system (WKT or IAU code)")
    dimensions: Optional[List[int]] = Field(None, description="[width, height] or [width, height, bands]")
    resolution: Optional[float] = Field(None, description="Native spatial resolution in meters per pixel")
    nominal_sensor_gsd_m: Optional[float] = Field(None, description="Nominal sensor ground sample distance at nadir (m)")
    effective_spatial_resolution_m: Optional[float] = Field(None, description="Effective optical/gridded spatial resolution accounting for atmospheric tau & processing (m)")
    epistemic_classification: Optional[str] = Field("OBSERVED", description="OBSERVED, MEASURED, DERIVED, MODEL_ESTIMATED, etc.")
    is_cloud_optimized_geotiff: Optional[bool] = Field(False, description="Whether the raster file has internal COG tiling and overviews")
    tile_integrity_checksum: Optional[str] = Field(None, description="SHA-256 verification hash for raster tiles")
    data_type: Optional[str] = Field(None, description="Numeric data type (Int16, Float32, Byte, etc.)")
    units: Optional[str] = Field(None, description="Physical units (meters, W/(m^2*sr*um), DN, etc.)")
    
    calibration: Optional[CalibrationInfo] = None
    spectral_information: Optional[SpectralInformation] = None
    nodata_policy: Optional[NoDataPolicy] = None
    
    source_archive: str = Field(..., description="Source planetary archive (NASA PDS, USGS, etc.)")
    source_uri: Optional[str] = Field(None, description="Source archive download URL or DOI")
    storage_path: Optional[str] = Field(None, description="Local storage path relative to repo root")
    checksum: Optional[FileProvenance] = Field(None, description="Primary data file SHA-256 integrity hash")
    
    processing_history: ProvenanceHistory = Field(default_factory=ProvenanceHistory)
    validation_status: ValidationStatus = Field(default=ValidationStatus.DISCOVERED)
    scientific_limitations: Optional[str] = Field(None, description="Explicit statement of scientific uncertainties")
    
    # Future-compatible extensible attributes for specialized instrument families
    family_attributes: Dict[str, Any] = Field(default_factory=dict)
