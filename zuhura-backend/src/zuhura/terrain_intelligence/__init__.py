"""
Terrain analysis package.
Implements geodetically sound, latitude-scaled morphometric derivatives,
great-circle geodesic transect profiling, and focal terrain statistics.
"""

from zuhura.terrain_intelligence.derivatives import (
    calculate_slope_and_aspect_horn,
    aspect_degrees_to_cardinal,
    calculate_profile_curvature,
)
from zuhura.terrain_intelligence.morphometry import (
    calculate_tri_roughness,
    calculate_tpi,
    classify_tpi,
    calculate_focal_relief,
    calculate_focal_statistics,
)
from zuhura.terrain_intelligence.profiler import (
    interpolate_geodesic_transect,
    compute_profile_summary,
)
from zuhura.terrain_intelligence.engine import (
    TerrainIntelligenceEngine,
    get_terrain_engine,
)

__all__ = [
    "calculate_slope_and_aspect_horn",
    "aspect_degrees_to_cardinal",
    "calculate_profile_curvature",
    "calculate_tri_roughness",
    "calculate_tpi",
    "classify_tpi",
    "calculate_focal_relief",
    "calculate_focal_statistics",
    "interpolate_geodesic_transect",
    "compute_profile_summary",
    "TerrainIntelligenceEngine",
    "get_terrain_engine",
]
