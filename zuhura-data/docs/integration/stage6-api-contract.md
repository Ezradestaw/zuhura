# Zuhura Mars Digital Twin — Stage 6 API Contract Specification

**Document Version:** 1.0.0  
**Phase:** Stage 6 Scientific Data & Backend Integration  
**Service:** `zuhura-backend` (FastAPI 0.115+)  
**Data Foundation:** `zuhura-data`  
**Reference Datum:** IAU/IAG 2015 Mars Biaxial Ellipsoid & MOLA GMM-3 Areoid  

---

## 1. Overview

This document specifies the RESTful scientific API endpoints connecting the Zuhura backend to the digital twin frontend (`zuhura-frontend`), data science services, and automated analysis engines.

All endpoints adhere to:
1. Planetary geodetic coordinates: Planetocentric latitude $[-90.0, +90.0]^\circ$ and East-positive longitude $[0.0, 360.0]^\circ$.
2. Topographic reference: MOLA GMM-3 equipotential areoid datum.
3. Path sanitization: Strict prevention of filesystem traversal.
4. Scientific integrity: Clear distinction between physical calibrated values and visualization-stretched pixels.

---

## 2. Scientific Elevation Service

### `GET /api/v1/elevation`
Retrieves the scientifically calibrated topographic elevation at any Martian coordinate directly from the global Cloud-Optimized GeoTIFF (`mola_global_meg128_cog.tif`).

#### Query Parameters
| Parameter | Type | Required | Description | Example |
|---|---|---|---|---|
| `latitude` | `float` | Conditional | Latitude in degrees $[-90, +90]$ | `18.38` |
| `longitude` | `float` | Conditional | Longitude in degrees East (wraps automatically) | `77.58` |
| `lat` | `float` | Conditional | Alias for `latitude` | `18.38` |
| `lon` | `float` | Conditional | Alias for `longitude` | `-282.42` |

#### Responses
- **200 OK**: Elevation query successful.
```json
{
  "latitude": 18.38,
  "longitude": 77.58,
  "elevation_m": -2534,
  "vertical_reference": "MOLA GMM-3 Areoid (Equipotential Reference Surface)",
  "datum": "MOLA GMM-3",
  "uncertainty_m": 1.0,
  "dataset_id": "zuhura-mola-global-v3-cog",
  "validation_status": "scientifically_validated",
  "nodata_status": false
}
```

- **200 OK (Out of Bounds / Polar Gap)**: Coordinates outside valid data range ($|\text{lat}| > 88.0^\circ$).
```json
{
  "latitude": 89.2,
  "longitude": 45.0,
  "elevation_m": null,
  "vertical_reference": "MOLA GMM-3 Areoid (Equipotential Reference Surface)",
  "datum": "MOLA GMM-3",
  "uncertainty_m": null,
  "dataset_id": "zuhura-mola-global-v3-cog",
  "validation_status": "outside_coverage_boundary",
  "nodata_status": true
}
```

- **400 Bad Request**: Missing latitude or longitude.

---

## 3. Scientific Product Catalog Service

### `GET /api/v1/catalog/search`
Multi-criteria discovery and spatial-temporal filtering across planetary products in `zuhura_science_catalog.json`.

#### Query Parameters
| Parameter | Type | Default | Description |
|---|---|---|---|
| `instrument` | `string` | `null` | Case-insensitive filter (e.g., `MOLA`, `THEMIS`, `CTX`, `HiRISE`) |
| `mission` | `string` | `null` | Mission name (e.g., `MGS`, `Mars Odyssey`, `MRO`) |
| `product_type` | `string` | `null` | `raster_elevation`, `raster_spectral`, `raster_imagery` |
| `product_level` | `string` | `null` | Data processing level (`PDS3_RDR`, `EDR`, `LEVEL2`) |
| `bbox` | `string` | `null` | Martian bounding box: `min_lon,min_lat,max_lon,max_lat` |
| `start_date` | `string` | `null` | ISO-8601 start date filter (`YYYY-MM-DD`) |
| `end_date` | `string` | `null` | ISO-8601 end date filter (`YYYY-MM-DD`) |
| `min_res` | `float` | `null` | Minimum spatial resolution in meters/pixel |
| `max_res` | `float` | `null` | Maximum spatial resolution in meters/pixel |
| `validation_status`| `string` | `null` | `scientifically_validated`, `unverified` |
| `page` | `int` | `1` | Page number ($\ge 1$) |
| `page_size` | `int` | `20` | Results per page ($1 \le \text{size} \le 100$) |

#### Responses
- **200 OK**:
```json
{
  "total": 13,
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "items": [
    {
      "product_id": "mola_global_meg128_cog",
      "dataset_id": "zuhura-mola-global-v3-cog",
      "title": "Global MOLA MEG128 Cloud-Optimized GeoTIFF Elevation Model",
      "instrument": "MOLA",
      "mission": "Mars Global Surveyor",
      "product_type": "raster_elevation",
      "spatial_extent": { "min_lon": 0.0, "min_lat": -88.0, "max_lon": 360.0, "max_lat": 88.0 },
      "resolution": 463.0577,
      "validation_status": "scientifically_validated"
    }
  ]
}
```

### `GET /api/v1/catalog/products/{product_id}`
Retrieves complete canonical metadata and provenance history for a single product.

---

## 4. Scientific Raster Metadata & Streaming

### `GET /api/v1/rasters/{product_id}/metadata`
Inspects low-level GDAL dataset characteristics.

#### Responses
- **200 OK**:
```json
{
  "product_id": "mola_global_meg128_cog",
  "storage_path": "data/processed/mola/mosaic/mola_global_meg128_cog.tif",
  "file_size_bytes": 1403212626,
  "dimensions": [46080, 22528, 1],
  "data_type": "Int16",
  "nodata_value": null,
  "overview_count": 7,
  "bounds": { "min_x": -10668612.9, "min_y": -5211925.3, "max_x": 10668612.9, "max_y": 5211925.3 },
  "geotransform": [-10668612.9, 463.0577, 0.0, 5211925.3, 0.0, -463.0577],
  "projection_wkt": "PROJCS[\"Mars_simpCyl_c180\"...]"
}
```

### `GET /api/v1/rasters/{product_id}`
Safely streams the binary raster asset over HTTP with chunked file streaming. Validates against directory traversal and verifies catalog membership.

---

## 5. Dynamic Map Tile Service

### `GET /api/v1/tiles/cog/{z}/{x}/{y}.png`
### `GET /api/v1/tiles/{product_id}/{z}/{x}/{y}.png`
Renders an on-the-fly 256×256 PNG map tile directly from the Cloud-Optimized GeoTIFF overview pyramids.

#### Query Parameters
| Parameter | Type | Default | Description |
|---|---|---|---|
| `colormap` | `string` | `terrain` | Colormap: `terrain`, `viridis`, `plasma`, `inferno`, `gray` |
| `scheme` | `string` | `geographic` | Tiling scheme: `geographic` (Cesium) or `webmercator` |
| `min_elev` | `float` | `-8200.0` | Minimum elevation for color ramp normalization |
| `max_elev` | `float` | `21200.0` | Maximum elevation for color ramp normalization |

#### Response Headers
- `Content-Type`: `image/png`
- `Cache-Control`: `public, max-age=86400`
- `X-Tile-Cache`: `HIT` or `MISS`

---

## 6. Quantized-Mesh 3D Terrain Service

### `GET /api/v1/tiles/terrain/jezero/layer.json`
Returns standard Cesium `layer.json` metadata for the Jezero regional terrain pyramid.

### `GET /api/v1/tiles/terrain/jezero/{z}/{x}/{y}.terrain`
Serves binary Cesium Quantized-Mesh 1.0 terrain tiles encoded with the IAU/IAG 2015 Mars Biaxial Ellipsoid.

#### Response Headers
- `Content-Type`: `application/vnd.quantized-mesh`
- `Cache-Control`: `public, max-age=86400`
