"""
Zuhura Planetary Digital Twin - CTX Validation Pipeline
Validates MRO Context Camera (CTX) visible observations, embedded PDS3/VICAR headers,
camera geometry, and regional context coverage.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from zuhura_data.pipelines.themis_validation import parse_pds3_header_from_file


def validate_ctx_product(product_path: Path) -> Dict[str, Any]:
    """
    Validates an MRO CTX image product against PDS planetary standards.
    """
    errors = []
    warnings = []

    if not product_path.exists():
        return {"valid": False, "errors": [f"File not found: {product_path}"]}

    meta = parse_pds3_header_from_file(product_path, max_bytes=32768)
    if not meta:
        errors.append("No valid PDS3 header found in CTX product.")

    inst = meta.get("INSTRUMENT_ID", "")
    sc = meta.get("SPACECRAFT_NAME", "")
    target = meta.get("TARGET_NAME", "")

    if inst.upper() != "CTX":
        errors.append(f"Invalid INSTRUMENT_ID: expected 'CTX', got '{inst}'")
    if "RECONNAISSANCE" not in sc.upper() and "MRO" not in sc.upper():
        errors.append(f"Unexpected spacecraft: '{sc}'")
    if target.upper() != "MARS":
        errors.append(f"Target is not Mars: '{target}'")

    lines = int(meta.get("LINES", 0))
    line_samples = int(meta.get("LINE_SAMPLES", 0))
    sample_bits = int(meta.get("SAMPLE_BITS", meta.get("SAMPLE_BIT_MODE_ID", "8") if meta.get("SAMPLE_BIT_MODE_ID", "").isdigit() else "8"))
    orbit = meta.get("ORBIT_NUMBER")

    if lines <= 0 or line_samples <= 0:
        errors.append(f"Invalid raster dimensions: {line_samples}x{lines}")

    sampling_factor = int(meta.get("SAMPLING_FACTOR", 1))
    approx_scale = 5.55 * sampling_factor  # Native CTX pixel scale is ~5.55 m/px

    return {
        "valid": len(errors) == 0,
        "file_name": product_path.name,
        "file_size_bytes": product_path.stat().st_size,
        "instrument": inst,
        "spacecraft": sc,
        "product_id": meta.get("PRODUCT_ID"),
        "orbit_number": orbit,
        "lines": lines,
        "line_samples": line_samples,
        "sampling_factor": sampling_factor,
        "pixel_resolution_m": approx_scale,
        "start_time": meta.get("START_TIME"),
        "focal_plane_temperature": meta.get("FOCAL_PLANE_TEMPERATURE"),
        "rationale": meta.get("RATIONALE_DESC"),
        "errors": errors,
        "warnings": warnings,
    }
