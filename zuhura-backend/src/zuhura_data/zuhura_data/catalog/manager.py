"""
Zuhura Planetary Digital Twin - Scientific Catalog Manager
Provides high-level catalog persistence, query interfaces, and synchronization.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from zuhura_data.models.catalog import ScientificCatalog
from zuhura_data.models.scientific_product import (
    DatasetFamily,
    ProductLevel,
    ProductType,
    ScientificProduct
)
from zuhura_data.models.spatial import BoundingBox
from zuhura_data.models.provenance import ValidationStatus


class CatalogManager:
    """
    Catalog manager facilitating persistence, fast spatial/temporal querying,
    and product lookups.
    """
    def __init__(self, catalog: Optional[ScientificCatalog] = None):
        self.catalog = catalog or ScientificCatalog()

    @classmethod
    def load_from_file(cls, path: Path) -> "CatalogManager":
        """Load catalog from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        cat = ScientificCatalog.model_validate(data)
        return cls(cat)

    def save_to_file(self, path: Path) -> None:
        """Serialize catalog to JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.catalog.model_dump(mode="json"), f, indent=2)

    def get_product(self, identifier: str) -> Optional[ScientificProduct]:
        """Lookup by dataset_id or archive product_id."""
        prod = self.catalog.get_by_id(identifier)
        if prod:
            return prod
        return self.catalog.get_by_product_id(identifier)

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
        time_start: Optional[Any] = None,
        time_end: Optional[Any] = None,
        bbox: Optional[BoundingBox] = None,
        point: Optional[Tuple[float, float]] = None,
        geometry_wkt: Optional[str] = None
    ) -> List[ScientificProduct]:
        """Search catalog across attributes, location, and time."""
        return self.catalog.search(
            family=family,
            mission=mission,
            instrument=instrument,
            product_level=product_level,
            product_type=product_type,
            validation_status=validation_status,
            min_resolution=min_resolution,
            max_resolution=max_resolution,
            time_start=time_start,
            time_end=time_end,
            bbox=bbox,
            point=point,
            geometry_wkt=geometry_wkt
        )

    def summary_statistics(self) -> Dict[str, Any]:
        """Generate high-level counts and breakdown across families and levels."""
        by_family = {}
        by_level = {}
        by_status = {}
        for p in self.catalog.products:
            f = p.dataset_family.value
            by_family[f] = by_family.get(f, 0) + 1
            lvl = p.product_level.value
            by_level[lvl] = by_level.get(lvl, 0) + 1
            st = p.validation_status.value
            by_status[st] = by_status.get(st, 0) + 1

        return {
            "total_products": self.catalog.product_count,
            "by_family": by_family,
            "by_product_level": by_level,
            "by_validation_status": by_status,
            "catalog_version": self.catalog.version,
            "geodetic_framework": self.catalog.geodetic_framework.model_dump()
        }
