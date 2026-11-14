import re
from typing import Dict, Any, List


def validate_dataset_metadata(record: Dict[str, Any]) -> List[str]:
    """
    Validates a scientific dataset metadata record against Zuhura planetary guidelines.
    Returns a list of error messages (empty if valid).
    """
    errors = []

    required_fields = [
        "id", "title", "description", "category", "processing_level",
        "provider", "original_url", "citation", "license", "crs_wkt",
        "spatial_extent", "spatial_resolution_m", "scientific_limitations"
    ]

    for field in required_fields:
        if field not in record or record[field] is None:
            errors.append(f"Missing required field: '{field}'")

    # ID format
    if "id" in record and not re.match(r"^[a-z0-9-_]+$", record["id"]):
        errors.append(f"Invalid dataset ID format: '{record['id']}'")

    # Spatial extent check
    extent = record.get("spatial_extent", {})
    for coord in ["min_lon", "max_lon", "min_lat", "max_lat"]:
        if coord not in extent:
            errors.append(f"Missing extent boundary: '{coord}'")

    if extent.get("min_lat", 0) > extent.get("max_lat", 0):
        errors.append("Spatial extent min_lat cannot exceed max_lat")

    if extent.get("latitude_convention") not in ["planetocentric", "planetographic"]:
        errors.append(f"Invalid latitude convention: '{extent.get('latitude_convention')}'")

    if extent.get("longitude_convention") not in ["east_positive", "west_positive"]:
        errors.append(f"Invalid longitude convention: '{extent.get('longitude_convention')}'")

    # Scientific limitations cannot be empty
    if not record.get("scientific_limitations", "").strip():
        errors.append("Scientific limitations statement must be provided to articulate uncertainty.")

    return errors
