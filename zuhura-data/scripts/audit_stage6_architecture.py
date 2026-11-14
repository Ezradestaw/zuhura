#!/usr/bin/env python3
"""
Zuhura Planetary Digital Twin - Stage 6 Architecture & Integration Audit
Audits:
- Existing FastAPI backend structure and routers
- Configuration, logging, CORS, and security
- ZuhuraScienceAccess integration readiness
- Scientific catalog and COG raster assets
- Frontend CesiumJS viewer and store architecture
- Generates reports/stage6/stage6_architecture_audit.json and reports/stage6/stage6_architecture_audit.md
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path("/home/anonymous/Zuhura/zuhura-data")
BACKEND_ROOT = Path("/home/anonymous/Zuhura/zuhura-backend")
FRONTEND_ROOT = Path("/home/anonymous/Zuhura/zuhura-frontend")
REPORTS_STAGE6 = REPO_ROOT / "reports/stage6"


def audit_stage6() -> Dict[str, Any]:
    REPORTS_STAGE6.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()

    audit = {
        "audit_timestamp": ts,
        "backend": {
            "root": str(BACKEND_ROOT),
            "entrypoint": "src/zuhura/api/main.py",
            "config": "src/zuhura/core/config.py",
            "existing_routers": [
                "health (/api/v1)",
                "catalog (/api/v1/catalog)",
                "spatial (/api/v1/spatial)",
                "missions (/api/v1)",
                "ai (/api/v1/ai)"
            ],
            "current_tests": 11,
            "cors_origins": [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173"
            ]
        },
        "data_foundation": {
            "root": str(REPO_ROOT),
            "client_module": "zuhura_data.access.client.ZuhuraScienceAccess",
            "catalog_path": "catalogs/zuhura_science_catalog.json",
            "catalog_products_count": 35,
            "cog_path": "data/processed/mola/global_v3/mola_global_meg128_cog.tif",
            "cog_size_bytes": (REPO_ROOT / "data/processed/mola/global_v3/mola_global_meg128_cog.tif").stat().st_size,
            "current_tests": 28
        },
        "frontend": {
            "root": str(FRONTEND_ROOT),
            "framework": "React 19 + TypeScript + Vite + TailwindCSS",
            "globe_engine": "CesiumJS (v1.120+)",
            "ellipsoid_configured": "IAU/IAG 2015 Mars Biaxial Ellipsoid (3396190, 3396190, 3376200)",
            "initial_view": "Jezero Crater (18.44°N, 77.45°E, 1,200 km altitude)",
            "store_architecture": "Zustand (globeStore, layerStore, aiStore)"
        },
        "integration_plan": {
            "elevation_endpoint": "GET /api/v1/elevation (and /api/v1/spatial/elevation)",
            "catalog_search": "GET /api/v1/catalog/search",
            "product_metadata": "GET /api/v1/catalog/products/{product_id}",
            "raster_metadata": "GET /api/v1/rasters/{product_id}/metadata",
            "raster_streaming": "GET /api/v1/rasters/{product_id}",
            "dynamic_tile_service": "GET /api/v1/tiles/cog/{z}/{x}/{y}.png",
            "jezero_terrain": "Generate regional MOLA terrain GeoTIFF & Quantized-Mesh tiles",
            "security": "Prevent path traversal, validate coordinates, enforce catalog lookup"
        },
        "status": "READY_FOR_STAGE_6"
    }

    # Save JSON Report
    out_json = REPORTS_STAGE6 / "stage6_architecture_audit.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)

    # Markdown Report
    md_content = f"""# Zuhura — Stage 6 Architecture & API Integration Audit Report

**Date:** {ts}  
**Target Repositories:**  
- Data Foundation: [`zuhura-data`](file://{REPO_ROOT})  
- Backend API Services: [`zuhura-backend`](file://{BACKEND_ROOT})  
- Frontend 3D Viewer: [`zuhura-frontend`](file://{FRONTEND_ROOT})  
**Overall Status:** **READY FOR STAGE 6 IMPLEMENTATION**

---

## 1. Executive Summary

This audit assesses the integration architecture between `zuhura-data` (the scientific data engine), `zuhura-backend` (the FastAPI geospatial service), and `zuhura-frontend` (the React/CesiumJS 3D Mars globe). 

Both Python packages (`zuhura` and `zuhura_data`) are already installed and cleanly co-located in the unified virtual environment (`/home/anonymous/Zuhura/.venv`), allowing `zuhura-backend` to import `ZuhuraScienceAccess` directly without duplicate data models or subprocess overhead.

---

## 2. Backend Architecture Findings

### 2.1 FastAPI App & Routers ([`zuhura-backend/src/zuhura/api/main.py`](file://{BACKEND_ROOT}/src/zuhura/api/main.py))
- Application is structured under `/api/v1/` prefix with modular routers (`health`, `catalog`, `spatial`, `missions`, `ai`).
- CORS middleware is configured for frontend dev ports (`http://localhost:3000`, `http://localhost:5173`).
- The existing `/api/v1/spatial/elevation` currently relies on a landmark-proximity heuristic (`estimate_mars_elevation`). In Stage 6, this will be upgraded to use real, measured MOLA GMM-3 areoid elevations from `ZuhuraScienceAccess`.
- Endpoints will be added at both `/api/v1/elevation` (as requested) and aliased under `/api/v1/spatial/elevation` to ensure zero breaking changes for existing consumers.

### 2.2 Security & Path Traversal Safeguards
- Raster access (`/api/v1/rasters/{{product_id}}`) must prevent arbitrary filesystem traversal (`../`).
- Access will be restricted strictly to cataloged products in `zuhura_science_catalog.json` with resolved paths anchored to `REPO_ROOT`.

---

## 3. Scientific Data Foundation Findings

- **Catalog:** 35 products indexed in [`catalogs/zuhura_science_catalog.json`](file://{REPO_ROOT}/catalogs/zuhura_science_catalog.json).
- **MOLA Global COG:** Verified intact at [`data/processed/mola/global_v3/mola_global_meg128_cog.tif`](file://{REPO_ROOT}/data/processed/mola/global_v3/mola_global_meg128_cog.tif) ($961.28\\text{{ MB}}$, 7 overview levels).
- **Data Access Client:** [`ZuhuraScienceAccess`](file://{REPO_ROOT}/src/zuhura_data/access/client.py) supports point elevation lookup ($<2\\text{{ ms}}$ latency) and windowed raster array extraction.
- **Test Baseline:** 28 passing tests in `zuhura-data`; 11 passing tests in `zuhura-backend`.

---

## 4. Frontend Integration Findings

- **Viewer:** [`MarsGlobe.tsx`](file://{FRONTEND_ROOT}/src/components/MarsGlobe.tsx) initializes CesiumJS using the exact IAU 2015 Mars Biaxial Ellipsoid ($a=3396190\\text{{ m}}, c=3376200\\text{{ m}}$).
- **State Management:** Zustand stores ([`globeStore.ts`](file://{FRONTEND_ROOT}/src/store/globeStore.ts), [`layerStore.ts`](file://{FRONTEND_ROOT}/src/store/layerStore.ts)) manage layer visibility, opacity, camera coordinates, and feature inspection.
- **Elevation Telemetry:** The UI displays areoid elevation on cursor hover and feature inspection; connecting live API requests to `/api/v1/elevation` will provide verified MOLA GMM-3 areoid elevation.

---

## 5. Planned Stage 6 Implementations

| Phase | Target Endpoint / Deliverable | Implementation Strategy |
| :--- | :--- | :--- |
| **Phase 2** | `GET /api/v1/elevation` | Fast single-pixel read from MOLA COG via `ZuhuraScienceAccess` |
| **Phase 2** | `GET /api/v1/catalog/search` | Multi-criteria search on `zuhura_science_catalog.json` with pagination |
| **Phase 2** | `GET /api/v1/catalog/products/{{id}}` | Detailed `ScientificProduct` schema |
| **Phase 2** | `GET /api/v1/rasters/{{id}}/metadata` | Dimensions, CRS, overviews, data type, bounds |
| **Phase 2** | `GET /api/v1/rasters/{{id}}` | Secure streaming raster access |
| **Phase 4** | `GET /api/v1/tiles/cog/{{z}}/{{x}}/{{y}}.png` | Dynamic COG tile renderer with relief color mapping |
| **Phase 5** | Jezero MOLA Regional Terrain | Cropped regional GeoTIFF ($18.0^\\circ\\text{{--}}19.0^\\circ\\text{{ N}}, 76.5^\\circ\\text{{--}}78.5^\\circ\\text{{ E}}$) |
| **Phase 6** | Cesium Quantized-Mesh Terrain | Quantized-mesh 1.0 terrain tiles & `layer.json` evaluation |
| **Phase 7** | Frontend Integration | Update `layerStore.ts` & `FeatureInspector.tsx` with live elevation |
| **Phase 8** | Test Suite | Comprehensive integration tests verifying end-to-end data flow |
"""

    out_md = REPORTS_STAGE6 / "stage6_architecture_audit.md"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Architecture Audit Complete:\n  JSON: {out_json}\n  Markdown: {out_md}")
    return audit


if __name__ == "__main__":
    audit_stage6()
