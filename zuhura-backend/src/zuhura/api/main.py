import time
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from zuhura.core.config import log_runtime_configuration_warnings, settings
from zuhura.core.metrics import record_request, generate_prometheus_metrics_text
from zuhura.core.security import SecurityHeadersMiddleware, RateLimitMiddleware
from zuhura.api.v1.health import router as health_router
from zuhura.api.v1.catalog import router as catalog_router
from zuhura.api.v1.spatial import router as spatial_router
from zuhura.api.v1.elevation import router as elevation_router
from zuhura.api.v1.rasters import router as rasters_router
from zuhura.api.v1.tiles import router as tiles_router
from zuhura.api.v1.missions import router as missions_router
from zuhura.api.v1.ai import router as ai_router
from zuhura.api.v1.illumination import router as illumination_router
from zuhura.api.v1.terrain import router as terrain_router
from zuhura.api.v1.navigation import router as navigation_router
from zuhura.api.v1.hover import router as hover_router
from zuhura.api.v1.pinpoint import router as pinpoint_router
from zuhura.api.v1.regions import router as regions_router
from zuhura.api.v1.provenance import router as provenance_router
from zuhura.api.v1.vision import router as vision_router
from zuhura.api.v1.workspace import router as workspace_router
from zuhura.api.v1.environment import router as environment_router
from zuhura.api.v1.rover import router as rover_router
from zuhura.api.v1.mount_sharp import router as mount_sharp_router

log_runtime_configuration_warnings()

app = FastAPI(
    title="Zuhura Mars Digital Twin & Scientific Intelligence API",
    version="1.0.0",
    description="Planetary GIS, STAC scientific catalog, spatial analysis, and grounded AI assistant for Mars.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Security, Rate Limiting & High-Performance Compression Middlewares
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure CORS
allow_all = "*" in settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app" if not allow_all else None,
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - t0
    record_request(request.method, request.url.path, response.status_code, duration)
    return response


@app.get("/metrics", summary="Prometheus Metrics Endpoint", tags=["System"])
async def get_metrics():
    """Returns application telemetry in standard Prometheus exposition format."""
    text = generate_prometheus_metrics_text()
    return Response(content=text, media_type="text/plain; version=0.0.4")

# Register API v1 Routers
app.include_router(health_router, prefix="/api/v1", tags=["System"])
app.include_router(elevation_router, prefix="/api/v1/elevation", tags=["Elevation"])
app.include_router(catalog_router, prefix="/api/v1/catalog", tags=["Catalog"])
app.include_router(spatial_router, prefix="/api/v1/spatial", tags=["Spatial"])
app.include_router(rasters_router, prefix="/api/v1/rasters", tags=["Rasters"])
app.include_router(tiles_router, prefix="/api/v1/tiles", tags=["Tiles"])
app.include_router(missions_router, prefix="/api/v1", tags=["Missions"])
app.include_router(ai_router, prefix="/api/v1/ai", tags=["AI"])
app.include_router(illumination_router, prefix="/api/v1/illumination", tags=["Illumination"])
app.include_router(terrain_router, prefix="/api/v1/spatial/terrain", tags=["Terrain Intelligence"])
app.include_router(navigation_router, prefix="/api/v1/spatial/navigation", tags=["Optimize Navigation"])
app.include_router(hover_router, prefix="/api/v1/spatial/hover", tags=["Hover Intelligence"])
app.include_router(pinpoint_router, prefix="/api/v1/spatial/pinpoint", tags=["Location Pinpoint"])
app.include_router(regions_router, prefix="/api/v1/spatial/regions", tags=["Mars Region Discovery"])
app.include_router(provenance_router, prefix="/api/v1/provenance", tags=["Scientific Truth Engine"])
app.include_router(vision_router, prefix="/api/v1/spatial/vision", tags=["Planetary Computer Vision & Visual Intelligence"])
app.include_router(workspace_router, prefix="/api/v1/spatial/workspace", tags=["Scientific Workspace & Operations"])
app.include_router(environment_router, prefix="/api/v1/spatial/environment", tags=["Planetary Environment & Atmospheric Simulation Lab"])
app.include_router(rover_router, prefix="/api/v1/rover", tags=["Mars Rovers & Surface Raw Images"])
app.include_router(mount_sharp_router, prefix="/api/v1/mount-sharp", tags=["Curiosity Mount Sharp"])


@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
async def root():
    return {
        "platform": "Zuhura Mars Digital Twin",
        "docs": "/docs",
        "version": "1.0.0",
        "reference_ellipsoid": "IAU/IAG 2015 WGCCRE"
    }
