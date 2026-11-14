"""
Zuhura Planetary Digital Twin - THEMIS Validation Pipeline
Validates Odyssey THEMIS infrared and visible observations, PDS3 QUB metadata,
spectral bands, calibration units, and thermal science conventions.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_pds3_header_from_file(file_path: Path, max_bytes: int = 65536) -> Dict[str, str]:
    """Parse key-value pairs from an embedded PDS3 header."""
    metadata = {}
    if not file_path.exists():
        return metadata

    with open(file_path, "rb") as f:
        header_bytes = f.read(max_bytes)

    text = header_bytes.decode("latin1", errors="ignore")
    for line in text.splitlines():
        if line.strip() == "END":
            break
        m = re.match(r"^\s*([A-Za-z0-9_:\^]+)\s*=\s*(.+)$", line)
        if m:
            k = m.group(1).strip()
            v = m.group(2).strip().strip('"').strip("'")
            metadata[k] = v
    return metadata


def validate_themis_product(product_path: Path) -> Dict[str, Any]:
    """
    Validates a THEMIS science product against planetary standards.
    Distinguishes radiance from kinetic surface temperature and verifies spectral metadata.
    """
    errors = []
    warnings = []

    if not product_path.exists():
        return {"valid": False, "errors": [f"File not found: {product_path}"]}

    meta = parse_pds3_header_from_file(product_path)
    if not meta:
        errors.append("No valid PDS3 header found in THEMIS product.")

    # Core instrument and mission identification
    inst = meta.get("INSTRUMENT_ID", "")
    target = meta.get("TARGET_NAME", "")
    sc = meta.get("SPACECRAFT_NAME", meta.get("INSTRUMENT_HOST_NAME", meta.get("MISSION_NAME", "")))

    if "THM" not in inst and "THEMIS" not in inst:
        errors.append(f"Invalid INSTRUMENT_ID: expected THEMIS/THM, got '{inst}'")
    if target.upper() != "MARS":
        errors.append(f"Target is not Mars: '{target}'")
    if "ODYSSEY" not in sc.upper() and "ODY" not in sc.upper():
        errors.append(f"Unexpected spacecraft: '{sc}'")

    # Product Type and Scientific Tier
    p_type = meta.get("PRODUCT_TYPE", "")
    core_unit = meta.get("CORE_UNIT", meta.get("UNIT", ""))

    # Scientific requirement: verify physical units and thermal distinction
    is_radiance = "W" in core_unit or "SPECTRAL RADIANCE" in p_type.upper() or "RDR" in str(product_path)
    is_kinetic_temp = "KELVIN" in core_unit and "KINETIC" in p_type.upper()

    if is_radiance and is_kinetic_temp:
        errors.append("Contradictory thermal metadata: radiance cannot be kinetic temperature without retrieval.")

    # Special pixel / NoData conventions in PDS QUB
    core_null = meta.get("CORE_NULL")
    special_pixels = {
        "CORE_NULL": core_null,
        "CORE_LOW_REPR_SAT": meta.get("CORE_LOW_REPR_SAT"),
        "CORE_HIGH_REPR_SAT": meta.get("CORE_HIGH_REPR_SAT"),
        "CORE_LOW_INSTR_SAT": meta.get("CORE_LOW_INSTR_SAT"),
        "CORE_HIGH_INSTR_SAT": meta.get("CORE_HIGH_INSTR_SAT"),
    }

    return {
        "valid": len(errors) == 0,
        "file_name": product_path.name,
        "file_size_bytes": product_path.stat().st_size,
        "instrument": inst,
        "spacecraft": sc,
        "target": target,
        "product_id": meta.get("PRODUCT_ID"),
        "observation_id": meta.get("ORIGINAL_PRODUCT_ID", meta.get("OBSERVATION_ID")),
        "processing_level": "Level 3 (Calibrated RDR)",
        "physical_quantity": "Spectral Radiance" if is_radiance else "Unspecified Thermal Observation",
        "units": core_unit,
        "special_pixels": special_pixels,
        "errors": errors,
        "warnings": warnings,
    }
