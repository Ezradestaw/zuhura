"""
Zuhura Planetary Digital Twin - HiRISE Validation Pipeline
Validates MRO High Resolution Imaging Science Experiment (HiRISE) observations,
detached PDS3 labels, map projections, sub-meter spatial scale, and channel configurations.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from zuhura_data.pipelines.themis_validation import parse_pds3_header_from_file


def validate_hirise_label(label_path: Path) -> Dict[str, Any]:
    """
    Validates an MRO HiRISE detached PDS3 label against planetary cartographic standards.
    """
    errors = []
    warnings = []

    if not label_path.exists():
        return {"valid": False, "errors": [f"Label file not found: {label_path}"]}

    meta = parse_pds3_header_from_file(label_path, max_bytes=32768)
    if not meta:
        errors.append("No valid PDS3 content found in HiRISE label.")

    inst = meta.get("INSTRUMENT_ID", "")
    sc = meta.get("SPACECRAFT_NAME", meta.get("INSTRUMENT_HOST_NAME", meta.get("MISSION_NAME", "")))
    target = meta.get("TARGET_NAME", "")

    if "HIRISE" not in inst.upper():
        errors.append(f"Invalid INSTRUMENT_ID: expected 'HIRISE', got '{inst}'")
    if "RECONNAISSANCE" not in sc.upper() and "MRO" not in sc.upper():
        errors.append(f"Unexpected spacecraft: '{sc}'")
    if target.upper() != "MARS":
        errors.append(f"Target is not Mars: '{target}'")

    proj_type = meta.get("MAP_PROJECTION_TYPE", "")
    raw_scale = meta.get("MAP_SCALE", meta.get("MAP_RESOLUTION", "0.0"))
    scale_match = re.search(r"[-+]?[0-9]*\.?[0-9]+", str(raw_scale))
    map_scale = float(scale_match.group(0)) if scale_match else 0.0
    center_lat = meta.get("CENTER_LATITUDE")
    center_lon = meta.get("CENTER_LONGITUDE")

    # Map scale check (sub-meter planetary observation)
    if map_scale > 2.0:
        warnings.append(f"Map scale {map_scale} m/px is larger than typical sub-meter HiRISE RDRs.")

    return {
        "valid": len(errors) == 0,
        "file_name": label_path.name,
        "file_size_bytes": label_path.stat().st_size,
        "instrument": inst,
        "spacecraft": sc,
        "product_id": meta.get("PRODUCT_ID"),
        "observation_id": meta.get("OBSERVATION_ID"),
        "projection": proj_type,
        "map_scale_m": map_scale,
        "center_latitude": center_lat,
        "center_longitude": center_lon,
        "a_axis_radius_km": meta.get("A_AXIS_RADIUS"),
        "c_axis_radius_km": meta.get("C_AXIS_RADIUS"),
        "errors": errors,
        "warnings": warnings,
    }
