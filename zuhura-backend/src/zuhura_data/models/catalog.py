"""
Zuhura Planetary Digital Twin - Unified Scientific Catalog Model
Manages the searchable repository catalog of Mars scientific datasets,
providing multi-criteria filtering across spatial, temporal, instrument, and quality axes.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from zuhura_data.models.scientific_product import (
    DatasetFamily,
    ProductLevel,
    ProductType,
    ScientificProduct
)
from zuhura_data.models.spatial import BoundingBox, SpatialCoverage
from zuhura_data.models.provenance import ValidationStatus


class GeodeticFramework(BaseModel):
    """Authoritative Mars geodetic reference framework."""
    ellipsoid_model: str = "IAU/IAG 2015 WGCCRE Mars Biaxial Ellipsoid"
    equatorial_radius_a_m: float = 3396190.0
    polar_radius_c_m: float = 3376200.0
    flattening: float = (3396190.0 - 3376200.0) / 3396190.0
    latitude_convention: str = "planetocentric"
    longitude_convention: str = "east_positive"
    vertical_datum: str = "MOLA GMM-3 Areoid (Potential Reference Surface)"


class ScientificCatalog(BaseModel):
    """
    Searchable, unified planetary catalog for Zuhura Mars Digital Twin.
    References existing processed and pilot products without data duplication.
    """
    catalog_name: str = "Zuhura Unified Planetary Scientific Catalog"
    version: str = "1.0.0"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    geodetic_framework: GeodeticFramework = Field(default_factory=GeodeticFramework)
    products: List[ScientificProduct] = Field(default_factory=list)

    @property
    def product_count(self) -> int:
        return len(self.products)

    def add_product(self, product: ScientificProduct) -> None:
        """Add or update a product in the catalog."""
        # Replace if dataset_id matches, else append
        for i, p in enumerate(self.products):
            if p.dataset_id == product.dataset_id:
                self.products[i] = product
                return
        self.products.append(product)

    def get_by_id(self, dataset_id: str) -> Optional[ScientificProduct]:
        """Lookup product by stable dataset_id."""
        for p in self.products:
            if p.dataset_id == dataset_id:
                return p
        return None

    def get_by_product_id(self, product_id: str) -> Optional[ScientificProduct]:
        """Lookup product by archive product_id."""
        for p in self.products:
            if p.product_id == product_id:
                return p
        return None

    def search(
        self,
        family: Optional[DatasetFamily] = None,
        mission: Optional[str] = None,
        instrument: Optional[str] = None,
        product_level: Optional[ProductLevel] = None,
        product_type: Optional[ProductType] = None,
        validation_status: Optional[ValidationStatus] = None,
        min_resolution: Optional[float] = None,
        max_resolution: Optional[float] = None,
        time_start: Optional[datetime] = None,
        time_end: Optional[datetime] = None,
        bbox: Optional[BoundingBox] = None,
        point: Optional[Tuple[float, float]] = None,  # (lat, lon)
        geometry_wkt: Optional[str] = None
    ) -> List[ScientificProduct]:
        """
        Multi-criteria search engine supporting attribute, temporal, and spatial filters.
        """
        results = []
        target_coverage = None
        if bbox:
            target_coverage = SpatialCoverage(bbox=bbox)
        elif geometry_wkt:
            # Create a mock bbox for the coverage wrapper
            target_coverage = SpatialCoverage(
                bbox=BoundingBox(min_lon=0, max_lon=360, min_lat=-90, max_lat=90),
                geometry_wkt=geometry_wkt
            )

        for p in self.products:
            # 1. Dataset Family Filter
            if family and p.dataset_family != family:
                continue

            # 2. Mission Filter
            if mission and mission.lower() not in p.mission.lower():
                continue

            # 3. Instrument Filter
            if instrument and instrument.upper() not in p.instrument.upper():
                continue

            # 4. Product Level Filter
            if product_level and p.product_level != product_level:
                continue

            # 5. Product Type Filter
            if product_type and p.product_type != product_type:
                continue

            # 6. Validation Status Filter
            if validation_status and p.validation_status != validation_status:
                continue

            # 7. Spatial Resolution Range (meters/pixel)
            if min_resolution is not None and p.resolution is not None:
                if p.resolution < min_resolution:
                    continue
            if max_resolution is not None and p.resolution is not None:
                if p.resolution > max_resolution:
                    continue

            # 8. Temporal Filter
            if time_start and p.acquisition_time:
                if p.acquisition_time < time_start:
                    continue
            if time_end and p.acquisition_time:
                if p.acquisition_time > time_end:
                    continue

            # 9. Spatial Point Containment
            if point is not None:
                lat, lon = point
                if not p.spatial_coverage.contains_point(lat, lon):
                    continue

            # 10. Spatial Coverage / Bounding Box Intersection
            if target_coverage is not None:
                if not p.spatial_coverage.intersects(target_coverage):
                    continue

            results.append(p)

        return results
