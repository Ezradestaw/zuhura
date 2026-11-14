import pytest
from zuhura_data.pipelines.validation import validate_dataset_metadata


def test_valid_dataset_metadata():
    sample = {
        "id": "zuhura-mola-megdr-128",
        "title": "MGS MOLA MEGDR 128 px/deg DEM",
        "description": "Global Mars elevation model.",
        "category": "topography",
        "processing_level": "derived_product",
        "provider": "NASA PDS Geosciences Node",
        "original_url": "https://pds-geosciences.wustl.edu/",
        "citation": "Smith et al. (2001)",
        "license": "NASA Open Data",
        "crs_wkt": "IAU:49900",
        "spatial_extent": {
            "min_lon": -180.0,
            "max_lon": 180.0,
            "min_lat": -90.0,
            "max_lat": 90.0,
            "latitude_convention": "planetocentric",
            "longitude_convention": "east_positive"
        },
        "spatial_resolution_m": 463.0,
        "scientific_limitations": "Along-track interpolation over poles."
    }
    errors = validate_dataset_metadata(sample)
    assert errors == []


def test_invalid_dataset_metadata_missing_fields():
    sample = {
        "id": "INVALID ID WITH SPACES",
        "spatial_extent": {
            "min_lat": 50.0,
            "max_lat": 10.0, # Inverted!
            "latitude_convention": "unknown_lat",
            "longitude_convention": "unknown_lon"
        }
    }
    errors = validate_dataset_metadata(sample)
    assert len(errors) > 0
    assert any("Missing required field" in e for e in errors)
    assert any("min_lat cannot exceed max_lat" in e for e in errors)
