#!/usr/bin/env python3
"""
Zuhura Planetary Digital Twin - Stage 5 Catalog Builder Executable
Constructs the unified scientific catalog from local products and discovered inventories.
Outputs to:
  - catalogs/zuhura_science_catalog.json
  - data/catalogs/zuhura_science_catalog.json
"""

import json
from pathlib import Path
from zuhura_data.catalog.builder import build_unified_catalog
from zuhura_data.catalog.manager import CatalogManager

REPO_ROOT = Path("/home/anonymous/Zuhura/zuhura-data")
OUT_FILE_1 = REPO_ROOT / "catalogs/zuhura_science_catalog.json"
OUT_FILE_2 = REPO_ROOT / "data/catalogs/zuhura_science_catalog.json"


def main():
    print("=" * 70)
    print("ZUHURA PLANETARY DATA PIPELINE: STAGE 5 CATALOG GENERATION")
    print("=" * 70)

    print("Building unified scientific catalog...")
    cat = build_unified_catalog()
    mgr = CatalogManager(cat)

    mgr.save_to_file(OUT_FILE_1)
    mgr.save_to_file(OUT_FILE_2)

    stats = mgr.summary_statistics()
    print(f"\nCatalog successfully written to:\n  1. {OUT_FILE_1}\n  2. {OUT_FILE_2}")
    print("\nCatalog Summary Statistics:")
    print(f"  Total Products Indexed: {stats['total_products']}")
    print(f"  By Family: {stats['by_family']}")
    print(f"  By Level: {stats['by_product_level']}")
    print(f"  By Validation Status: {stats['by_validation_status']}")


if __name__ == "__main__":
    main()
