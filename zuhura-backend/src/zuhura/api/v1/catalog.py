import math
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from zuhura.api.deps import get_science_access
from zuhura.core.config import settings
from zuhura_data.access.client import ZuhuraScienceAccess
from zuhura_data.models.spatial import BoundingBox
from zuhura_data.models.scientific_product import (
    DatasetFamily,
    ProductLevel,
    ProductType
)
from zuhura_data.models.provenance import ValidationStatus

router = APIRouter()

# Authoritative Initial Catalog of Verified Datasets
INITIAL_DATASETS = [
    {
        "id": "zuhura-mola-megdr-128",
        "title": "MGS MOLA Mission Experiment Gridded Data Record (MEGDR 128 px/deg)",
        "description": "Global Mars Digital Elevation Model (DEM) produced by the Mars Orbiter Laser Altimeter team. Referenced to the Mars MOLA GMM-2B Areoid.",
        "category": "topography",
        "processing_level": "derived_product",
        "mission": "Mars Global Surveyor",
        "instrument": "MOLA",
        "provider": "NASA Planetary Data System (PDS) Geosciences Node",
        "original_url": "https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/meg128/",
        "citation": "Smith, D. E., et al. (2001). Mars Orbiter Laser Altimeter: Experiment summary and selected results with data from the primary mission. Journal of Geophysical Research: Planets, 106(E10), 23689-23722.",
        "license": "NASA Open Data / Public Domain",
        "crs_wkt": "IAU:49900",
        "spatial_extent": {
            "min_lon": -180.0,
            "max_lon": 180.0,
            "min_lat": -90.0,
            "max_lat": 90.0,
            "longitude_convention": "east_positive",
            "latitude_convention": "planetocentric"
        },
        "spatial_resolution_m": 463.0,
        "elevation_datum": "Mars Areoid (MOLA GMM-2B)",
        "scientific_limitations": "Laser spot size of ~160m at surface, spacing ~300m along-track. Interpolated across polar winter data gaps.",
        "assets": {
            "terrain_tiles": {
                "href": "http://localhost:9000/zuhura-terrain/mola/{z}/{x}/{y}.terrain",
                "type": "application/vnd.quantized-mesh"
            },
            "colorized_relief": {
                "href": "http://localhost:9000/zuhura-tiles/mola-color/{z}/{x}/{y}.png",
                "type": "image/png"
            }
        },
        "last_verified_at": "2026-11-01T00:00:00Z"
    },
    {
        "id": "zuhura-viking-mdim21",
        "title": "Viking Orbiter Mars Digital Image Mosaic (MDIM 2.1)",
        "description": "Global orthorectified black and white visual image mosaic created from Viking Orbiter 1 and 2 framing cameras, calibrated to the MOLA coordinate reference system.",
        "category": "imagery",
        "processing_level": "derived_product",
        "mission": "Viking",
        "instrument": "Visual Imaging Subsystem (VIS)",
        "provider": "USGS Astrogeology Science Center",
        "original_url": "https://astrogeology.usgs.gov/search/map/Mars/Viking/MDIM21",
        "citation": "Archinal, B. A., et al. (2003). Mars Digital Image Mosaic 2.1 (MDIM 2.1). USGS Open-File Report.",
        "license": "USGS / Public Domain",
        "crs_wkt": "IAU:49900",
        "spatial_extent": {
            "min_lon": -180.0,
            "max_lon": 180.0,
            "min_lat": -90.0,
            "max_lat": 90.0,
            "longitude_convention": "east_positive",
            "latitude_convention": "planetocentric"
        },
        "spatial_resolution_m": 231.0,
        "elevation_datum": "None (Visual Surface Reflectance)",
        "scientific_limitations": "Acquired between 1976 and 1980 under varied illumination and dust optical depths; seamlines visible in high-contrast terrains.",
        "assets": {
            "visual_tiles": {
                "href": "http://localhost:9000/zuhura-tiles/viking-mdim21/{z}/{x}/{y}.png",
                "type": "image/png"
            }
        },
        "last_verified_at": "2026-11-01T00:00:00Z"
    },
    {
        "id": "zuhura-usgs-sim3292",
        "title": "Geologic Map of Mars (USGS Scientific Investigations Map 3292)",
        "description": "Comprehensive 1:20,000,000-scale global geologic map of Mars synthesizing decades of orbital observations (MGS, Odyssey, Mars Express, MRO).",
        "category": "geology",
        "processing_level": "interpretation",
        "mission": "Multi-Mission Synthesis",
        "instrument": "Multi-Instrument",
        "provider": "USGS Astrogeology Science Center",
        "original_url": "https://pubs.usgs.gov/sim/3292/",
        "citation": "Tanaka, K. L., et al. (2014). Geologic map of Mars (SIM 3292). U.S. Geological Survey.",
        "license": "USGS / Public Domain",
        "crs_wkt": "IAU:49900",
        "spatial_extent": {
            "min_lon": -180.0,
            "max_lon": 180.0,
            "min_lat": -90.0,
            "max_lat": 90.0,
            "longitude_convention": "east_positive",
            "latitude_convention": "planetocentric"
        },
        "spatial_resolution_m": 1000.0,
        "elevation_datum": "Mars Areoid (MOLA GMM-2B)",
        "scientific_limitations": "Interpretative stratigraphic units based on morphologic and thermal boundaries; subject to revision with higher-resolution spectroscopy.",
        "assets": {
            "vector_geojson": {
                "href": "http://localhost:9000/zuhura-tiles/geology-sim3292/units.geojson",
                "type": "application/geo+json"
            }
        },
        "last_verified_at": "2026-11-01T00:00:00Z"
    },
    {
        "id": "zuhura-jezero-hirise-mosaic",
        "title": "Jezero Crater Perseverance Landing Site HiRISE Controlled Mosaic",
        "description": "High-resolution orthorectified mosaic of Jezero Crater delta and landing ellipse captured by MRO HiRISE.",
        "category": "imagery",
        "processing_level": "derived_product",
        "mission": "Mars Reconnaissance Orbiter",
        "instrument": "HiRISE",
        "provider": "USGS Astrogeology / NASA PDS",
        "original_url": "https://astrogeology.usgs.gov/search/map/Mars/Mars2020/Jezero_HiRISE_Mosaic",
        "citation": "Fergason, R. L., et al. (2020). Mars 2020 Landing Site: Geologic Map and Mosaic Products. LPSC LI, Abstract #1024.",
        "license": "NASA / Public Domain",
        "crs_wkt": "IAU:49902",
        "spatial_extent": {
            "min_lon": 77.0,
            "max_lon": 77.8,
            "min_lat": 18.0,
            "max_lat": 18.8,
            "longitude_convention": "east_positive",
            "latitude_convention": "planetocentric"
        },
        "spatial_resolution_m": 0.25,
        "elevation_datum": "Mars Areoid (MOLA GMM-2B)",
        "scientific_limitations": "Local targeted coverage footprint limited to Jezero Crater interior and Western Fan delta.",
        "assets": {
            "cog": {
                "href": "http://localhost:9000/zuhura-cogs/jezero_hirise_mosaic.tif",
                "type": "image/tiff; application=geotiff; profile=cloud-optimized"
            }
        },
        "last_verified_at": "2026-11-01T00:00:00Z"
    }
]


@router.get("/datasets", summary="List and Search Scientific Datasets")
async def list_datasets(
    category: Optional[str] = Query(None, description="Scientific category filter"),
    mission: Optional[str] = Query(None, description="Spacecraft mission filter"),
    max_resolution_m: Optional[float] = Query(None, description="Maximum spatial resolution in meters"),
):
    """Returns catalog of scientific datasets matching query criteria."""
    results = INITIAL_DATASETS
    if category:
        results = [d for d in results if d["category"] == category]
    if mission:
        results = [d for d in results if mission.lower() in d["mission"].lower()]
    if max_resolution_m is not None:
        results = [d for d in results if d["spatial_resolution_m"] <= max_resolution_m]

    return {
        "total": len(results),
        "datasets": results,
    }


@router.get("/datasets/{dataset_id}", summary="Get Dataset by ID")
async def get_dataset(dataset_id: str):
    """Retrieves full metadata for a specific dataset."""
    for d in INITIAL_DATASETS:
        if d["id"] == dataset_id:
            return d
    raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")


@router.get("/search", summary="Search Unified Scientific Catalog")
async def search_catalog(
    instrument: Optional[str] = Query(None, description="Instrument acronym (e.g. THEMIS, CTX, HiRISE, MOLA)"),
    mission: Optional[str] = Query(None, description="Mission name filter"),
    family: Optional[str] = Query(None, description="Dataset family (mola, themis, ctx, hirise, viking_mdim)"),
    product_type: Optional[str] = Query(None, description="Product type (raster_elevation, raster_imagery, spectral_cube)"),
    product_level: Optional[str] = Query(None, description="Processing level (calibrated, map_projected, mosaic, etc.)"),
    validation_status: Optional[str] = Query(None, description="Validation status (scientifically_validated, discovered)"),
    bbox: Optional[str] = Query(None, description="Bounding box formatted as 'min_lon,min_lat,max_lon,max_lat'"),
    time_start: Optional[datetime] = Query(None, description="Start acquisition time (ISO 8601 UTC)"),
    time_end: Optional[datetime] = Query(None, description="End acquisition time (ISO 8601 UTC)"),
    min_resolution: Optional[float] = Query(None, description="Minimum spatial resolution in meters"),
    max_resolution: Optional[float] = Query(None, description="Maximum spatial resolution in meters"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    science_access: ZuhuraScienceAccess = Depends(get_science_access)
):
    """
    Search the unified Mars scientific product catalog across multi-dimensional criteria
    including geographic bounding box, time intervals, instrument, and quality status.
    """
    # Parse Bounding Box if provided
    bbox_obj = None
    if bbox:
        try:
            parts = [float(x.strip()) for x in bbox.split(",")]
            if len(parts) != 4:
                raise ValueError()
            bbox_obj = BoundingBox(
                min_lon=parts[0],
                min_lat=parts[1],
                max_lon=parts[2],
                max_lat=parts[3]
            )
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid 'bbox' format: expected 'min_lon,min_lat,max_lon,max_lat' (e.g. '76.5,18.0,78.5,19.0')."
            )

    # Convert string enums if valid
    fam_enum = DatasetFamily(family) if family in [e.value for e in DatasetFamily] else None
    lvl_enum = ProductLevel(product_level) if product_level in [e.value for e in ProductLevel] else None
    type_enum = ProductType(product_type) if product_type in [e.value for e in ProductType] else None
    status_enum = ValidationStatus(validation_status) if validation_status in [e.value for e in ValidationStatus] else None

    results = science_access.manager.search(
        family=fam_enum,
        mission=mission,
        instrument=instrument,
        product_level=lvl_enum,
        product_type=type_enum,
        validation_status=status_enum,
        min_resolution=min_resolution,
        max_resolution=max_resolution,
        time_start=time_start,
        time_end=time_end,
        bbox=bbox_obj
    )

    total_count = len(results)
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
    start_idx = (page - 1) * page_size
    paged_items = results[start_idx : start_idx + page_size]

    return {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "items": [p.model_dump(mode="json") for p in paged_items]
    }


@router.get("/products/{product_id}", summary="Get Canonical Scientific Product Metadata")
async def get_product_metadata(
    product_id: str,
    science_access: ZuhuraScienceAccess = Depends(get_science_access)
):
    """
    Retrieves complete canonical scientific metadata for a specific observation or mosaic
    from the unified catalog (lookup by product_id or dataset_id).
    """
    prod = science_access.get_product(product_id)
    if not prod:
        raise HTTPException(
            status_code=404,
            detail=f"Scientific product '{product_id}' not found in unified catalog."
        )
    return prod.model_dump(mode="json")


@router.get("/trek", summary="Search authentic NASA Mars Trek layers catalog")
async def get_mars_trek_catalog(
    category: Optional[str] = Query(None, description="Category: Imagery, Topography, Terrain, Mineral, ThermalInertia, Polar"),
    mission: Optional[str] = Query(None, description="Mission name filter"),
    instrument: Optional[str] = Query(None, description="Instrument name filter (e.g. MOLA, CTX, HiRISE, TES, HRSC, THEMIS)"),
    query: Optional[str] = Query(None, description="Text query across title, label, description"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200)
):
    """
    Returns authentic Mars Trek layer catalog with direct WMTS streaming endpoints,
    spatial bounding boxes, projection strings, and source attribution.
    """
    import json
    from pathlib import Path
    trek_path = Path(settings.MARS_DATA_ROOT) / "metadata" / "mars_trek_catalog.json"
    if not trek_path.exists():
        return {"total": 0, "page": page, "page_size": page_size, "total_pages": 0, "layers": []}

    with open(trek_path, "r") as f:
        layers = json.load(f)

    if category:
        cat_lower = category.lower()
        layers = [l for l in layers if l.get("category", "").lower() == cat_lower]

    if mission:
        mis_lower = mission.lower()
        layers = [l for l in layers if mis_lower in l.get("mission", "").lower()]

    if instrument:
        inst_lower = instrument.lower()
        layers = [l for l in layers if inst_lower in (l.get("instrument") or "").lower()]

    if query:
        q_lower = query.lower()
        layers = [
            l for l in layers
            if q_lower in l.get("title", "").lower()
            or q_lower in l.get("label", "").lower()
            or q_lower in (l.get("description") or "").lower()
        ]

    total = len(layers)
    total_pages = max(1, math.ceil(total / page_size))
    start_idx = (page - 1) * page_size
    paged = layers[start_idx : start_idx + page_size]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "layers": paged
    }


@router.get("/geology", summary="Get USGS SIM 3292 Geologic Map units and publication data")
async def get_geology_catalog():
    """
    Returns USGS SIM 3292 Global Chronostratigraphic units, ages (Noachian, Hesperian, Amazonian),
    descriptions, and downloadable publication pamphlets.
    """
    import json
    from pathlib import Path
    geo_path = Path(settings.MARS_DATA_ROOT) / "geology" / "usgs_sim3292_catalog.json"
    if not geo_path.exists():
        raise HTTPException(status_code=404, detail="USGS geology catalog not found")

    with open(geo_path, "r") as f:
        data = json.load(f)
    return data


@router.get("/craters", summary="Authoritative Mars impact craters and landmark catalog")
async def get_craters_catalog(
    min_diameter_km: Optional[float] = Query(None, description="Minimum crater diameter in km"),
    query: Optional[str] = Query(None, description="Search crater or structure name")
):
    """
    Returns authentic catalog of primary Martian impact basins, craters, and calderas
    referenced to IAU / USGS Gazetteer and Robbins & Hynek (2012).
    """
    craters = [
        {"name": "Hellas Planitia", "type": "Impact Basin", "diameter_km": 2300.0, "lat": -42.4, "lon": 70.5, "depth_m": 7152.0, "era": "Early Noachian", "description": "Deepest impact basin on Mars, reaching over 7 km below the datum."},
        {"name": "Argyre Planitia", "type": "Impact Basin", "diameter_km": 800.0, "lat": -49.7, "lon": 316.0, "depth_m": 5200.0, "era": "Early Noachian", "description": "Well-preserved giant multi-ring impact basin in the southern highlands."},
        {"name": "Isidis Planitia", "type": "Impact Basin", "diameter_km": 1500.0, "lat": 12.9, "lon": 87.0, "depth_m": 3800.0, "era": "Noachian", "description": "Vast circular impact plain adjacent to Syrtis Major and Jezero Crater."},
        {"name": "Gale Crater", "type": "Complex Crater", "diameter_km": 154.0, "lat": -4.59, "lon": 137.44, "depth_m": 5000.0, "era": "Late Noachian / Early Hesperian", "description": "Curiosity exploration site featuring Mount Sharp central mound."},
        {"name": "Jezero Crater", "type": "Deltaic Crater", "diameter_km": 49.0, "lat": 18.44, "lon": 77.45, "depth_m": 2570.0, "era": "Noachian", "description": "Perseverance rover landing site with ancient river delta and clay deposits."},
        {"name": "Gusev Crater", "type": "Paleolake Crater", "diameter_km": 166.0, "lat": -14.57, "lon": 175.47, "depth_m": 2100.0, "era": "Late Noachian", "description": "Spirit rover landing site fed by Ma'adim Vallis catastrophic outflow."},
        {"name": "Olympus Mons Caldera", "type": "Volcanic Caldera", "diameter_km": 80.0, "lat": 18.65, "lon": 226.2, "depth_m": 3200.0, "era": "Amazonian", "description": "Multi-collapsed summit calderas atop the solar system's tallest volcano (+21.2 km)."},
        {"name": "Korolev Crater", "type": "Ice-Filled Crater", "diameter_km": 81.4, "lat": 73.0, "lon": 164.5, "depth_m": 2000.0, "era": "Hesperian", "description": "Vast northern polar cold-trap reservoir containing ~2,200 km³ of perennial water ice."}
    ]

    if min_diameter_km is not None:
        craters = [c for c in craters if c["diameter_km"] >= min_diameter_km]

    if query:
        q = query.lower()
        craters = [c for c in craters if q in c["name"].lower() or q in c["type"].lower() or q in c["description"].lower()]

    return {"count": len(craters), "craters": craters}

