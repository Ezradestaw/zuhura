"""
Zuhura Planetary Digital Twin - Spatial Alignment & Multi-Instrument Overlap
Calculates precise geometric intersections, surface area in km^2 on the Mars ellipsoid,
overlap percentages, and cross-instrument spatial coverage matrices.
"""

import math
from typing import Any, Dict, List, Optional, Tuple
try:
    from osgeo import ogr
except ImportError:
    ogr = None  # type: ignore

# IAU 2015 Mars Ellipsoidal Constants
MARS_A_M = 3396190.0
MARS_C_M = 3376200.0


def deg2_to_km2_at_latitude(area_deg2: float, mean_lat_deg: float) -> float:
    """
    Convert square degrees to square kilometers on the IAU 2015 Mars ellipsoid
    at a specific planetocentric latitude.
    """
    lat_rad = math.radians(mean_lat_deg)
    # Radii of curvature
    e2 = (MARS_A_M**2 - MARS_C_M**2) / (MARS_A_M**2)
    # Meridional radius of curvature (North-South)
    M = (MARS_A_M * (1.0 - e2)) / math.pow(1.0 - e2 * (math.sin(lat_rad)**2), 1.5)
    # Prime vertical radius of curvature (East-West)
    N = MARS_A_M / math.sqrt(1.0 - e2 * (math.sin(lat_rad)**2))
    
    # Distance in km per degree
    km_per_lat_deg = math.radians(1.0) * M / 1000.0
    km_per_lon_deg = math.radians(1.0) * N * math.cos(lat_rad) / 1000.0
    
    km2_per_deg2 = km_per_lat_deg * km_per_lon_deg
    return area_deg2 * km2_per_deg2


def calculate_polygon_overlap(wkt1: str, wkt2: str, reference_lat_deg: float = 18.5) -> Dict[str, Any]:
    """
    Computes rigorous polygon intersection between two Mars WKT geometries.
    Returns intersection area in deg^2, km^2, and relative overlap percentages.
    """
    if ogr is None:
        return {"intersects": False, "error": "GDAL/OGR unavailable in runtime environment"}
    g1 = ogr.CreateGeometryFromWkt(wkt1)
    g2 = ogr.CreateGeometryFromWkt(wkt2)
    
    if not g1 or not g2:
        return {"intersects": False, "error": "Invalid WKT geometry"}
        
    area1_deg2 = g1.GetArea()
    area2_deg2 = g2.GetArea()
    
    if not g1.Intersects(g2):
        return {
            "intersects": False,
            "intersection_wkt": None,
            "intersection_area_deg2": 0.0,
            "intersection_area_km2": 0.0,
            "overlap_percent_of_g1": 0.0,
            "overlap_percent_of_g2": 0.0
        }
        
    inter = g1.Intersection(g2)
    inter_area_deg2 = inter.GetArea() if inter else 0.0
    inter_area_km2 = deg2_to_km2_at_latitude(inter_area_deg2, reference_lat_deg)
    
    return {
        "intersects": True,
        "intersection_wkt": inter.ExportToWkt() if inter else None,
        "intersection_area_deg2": round(inter_area_deg2, 6),
        "intersection_area_km2": round(inter_area_km2, 3),
        "overlap_percent_of_g1": round((inter_area_deg2 / area1_deg2) * 100.0, 2) if area1_deg2 > 0 else 0.0,
        "overlap_percent_of_g2": round((inter_area_deg2 / area2_deg2) * 100.0, 2) if area2_deg2 > 0 else 0.0
    }


def analyze_jezero_pilot_spatial_alignment(
    pilot_geometries: Dict[str, str],
    target_box_wkt: str,
    target_lat: float = 18.5
) -> Dict[str, Any]:
    """
    Performs cross-instrument spatial analysis across MOLA, THEMIS, CTX, and HiRISE
    pilot observations over Jezero Crater.
    """
    g_target = ogr.CreateGeometryFromWkt(target_box_wkt)
    target_area_deg2 = g_target.GetArea()
    target_area_km2 = deg2_to_km2_at_latitude(target_area_deg2, target_lat)
    
    coverage_summary = {}
    for name, wkt in pilot_geometries.items():
        g = ogr.CreateGeometryFromWkt(wkt)
        area_deg2 = g.GetArea() if g else 0.0
        area_km2 = deg2_to_km2_at_latitude(area_deg2, target_lat)
        
        # Intersect with target box
        inter_target = g.Intersection(g_target) if g else None
        target_cov_deg2 = inter_target.GetArea() if inter_target else 0.0
        target_cov_km2 = deg2_to_km2_at_latitude(target_cov_deg2, target_lat)
        
        coverage_summary[name] = {
            "total_footprint_deg2": round(area_deg2, 6),
            "total_footprint_km2": round(area_km2, 2),
            "coverage_in_target_box_deg2": round(target_cov_deg2, 6),
            "coverage_in_target_box_km2": round(target_cov_km2, 2),
            "percent_of_target_box": round((target_cov_deg2 / target_area_deg2) * 100.0, 2)
        }
        
    # Pairwise intersections
    pairwise = {}
    inst_names = list(pilot_geometries.keys())
    for i in range(len(inst_names)):
        for j in range(i + 1, len(inst_names)):
            n1 = inst_names[i]
            n2 = inst_names[j]
            pair_key = f"{n1}__vs__{n2}"
            res = calculate_polygon_overlap(pilot_geometries[n1], pilot_geometries[n2], target_lat)
            pairwise[pair_key] = res
            
    # Multi-way overlap (Intersection of all provided instruments)
    inter_all = g_target
    for wkt in pilot_geometries.values():
        g = ogr.CreateGeometryFromWkt(wkt)
        if inter_all and g:
            inter_all = inter_all.Intersection(g)
            
    multi_way_deg2 = inter_all.GetArea() if inter_all else 0.0
    multi_way_km2 = deg2_to_km2_at_latitude(multi_way_deg2, target_lat)
    
    return {
        "target_region": {
            "name": "Jezero Crater Western Delta",
            "bounding_box_wkt": target_box_wkt,
            "target_area_deg2": round(target_area_deg2, 4),
            "target_area_km2": round(target_area_km2, 2),
            "center_latitude_deg": target_lat
        },
        "instrument_coverage": coverage_summary,
        "pairwise_intersections": pairwise,
        "multi_instrument_coincident_coverage": {
            "all_instruments_intersect": multi_way_deg2 > 0.0,
            "coincident_area_deg2": round(multi_way_deg2, 6),
            "coincident_area_km2": round(multi_way_km2, 3),
            "coincident_area_acres": round(multi_way_km2 * 247.105, 1),
            "percent_of_target_box": round((multi_way_deg2 / target_area_deg2) * 100.0, 3)
        }
    }
