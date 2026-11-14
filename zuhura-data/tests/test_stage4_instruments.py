"""
Tests for Stage 4: THEMIS, CTX, and HiRISE scientific datasets.
Validates metadata discovery, catalog inventories, pilot file integrity, and instrument validations.
"""

import json
from pathlib import Path
import pytest

from zuhura_data.pipelines.themis_validation import validate_themis_product
from zuhura_data.pipelines.ctx_validation import validate_ctx_product
from zuhura_data.pipelines.hirise_validation import validate_hirise_label

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOGS_DIR = REPO_ROOT / "catalogs"
THEMIS_DIR = REPO_ROOT / "data/raw/themis"
CTX_DIR = REPO_ROOT / "data/raw/ctx"
HIRISE_DIR = REPO_ROOT / "data/raw/hirise"


def test_catalogs_exist_and_populated():
    """Verify machine-readable inventories were created for all three instruments."""
    for inst in ["themis", "ctx", "hirise"]:
        cat_file = CATALOGS_DIR / f"{inst}_jezero_inventory.json"
        assert cat_file.exists(), f"Missing catalog for {inst}: {cat_file}"

        with open(cat_file, "r") as f:
            data = json.load(f)

        assert data["count"] > 0, f"No products found in {inst} catalog"
        assert len(data["products"]) == data["count"]


def test_pilot_acquisition_manifest():
    """Verify pilot acquisition manifest records all three instruments."""
    manifest_file = CATALOGS_DIR / "pilot_acquisition_manifest.json"
    assert manifest_file.exists(), "Missing pilot acquisition manifest"

    with open(manifest_file, "r") as f:
        data = json.load(f)

    pilot_prods = data.get("pilot_products", {})
    assert "THEMIS" in pilot_prods
    assert "CTX" in pilot_prods
    assert "HiRISE" in pilot_prods

    # Verify each recorded file exists on disk and has matching size
    for inst, pinfo in pilot_prods.items():
        for fentry in pinfo["files"]:
            fpath = Path(fentry["path"])
            assert fpath.exists(), f"Pilot file missing on disk: {fpath}"
            assert fpath.stat().st_size == fentry["size_bytes"]
            assert len(fentry["sha256"]) == 64


def test_themis_pilot_validation():
    """Validate THEMIS pilot observation QUB."""
    themis_file = THEMIS_DIR / "I02413002RDR.QUB"
    assert themis_file.exists(), f"Missing THEMIS file: {themis_file}"

    res = validate_themis_product(themis_file)
    assert res["valid"], f"THEMIS validation failed: {res.get('errors')}"
    assert "THEMIS" in res["instrument"] or "THM" in res["instrument"]
    assert res["target"] == "MARS"
    assert res["physical_quantity"] == "Spectral Radiance"


def test_ctx_pilot_validation():
    """Validate CTX pilot observation IMG."""
    ctx_file = CTX_DIR / "P02_001820_1984_XI_18N282W.IMG"
    assert ctx_file.exists(), f"Missing CTX file: {ctx_file}"

    res = validate_ctx_product(ctx_file)
    assert res["valid"], f"CTX validation failed: {res.get('errors')}"
    assert res["instrument"] == "CTX"
    assert res["lines"] > 0 and res["line_samples"] > 0
    assert 5.0 <= res["pixel_resolution_m"] <= 7.0  # Approx 5.55 m/px


def test_hirise_pilot_validation():
    """Validate HiRISE pilot observation detached PDS labels."""
    hirise_mrgb_lbl = HIRISE_DIR / "PSP_004299_1985_MRGB.LBL"
    assert hirise_mrgb_lbl.exists(), f"Missing HiRISE label: {hirise_mrgb_lbl}"

    res = validate_hirise_label(hirise_mrgb_lbl)
    assert res["valid"], f"HiRISE validation failed: {res.get('errors')}"
    assert "HIRISE" in res["instrument"]
    assert res["product_id"] == "PSP_004299_1985_MRGB"
    assert res["map_scale_m"] <= 1.0  # Sub-meter scale


def test_shared_spatial_overlap_jezero():
    """Verify that all three pilot observations overlap Jezero Crater (18-19N, 77-78E)."""
    manifest_file = CATALOGS_DIR / "pilot_acquisition_manifest.json"
    with open(manifest_file, "r") as f:
        data = json.load(f)

    prods = data["pilot_products"]
    for inst in ["THEMIS", "CTX", "HiRISE"]:
        coords = prods[inst]["center_coordinates"]
        lat = coords["lat"]
        lon = coords["lon"]
        assert 17.5 <= lat <= 19.5, f"{inst} latitude {lat} outside Jezero region"
        assert 76.5 <= lon <= 78.5, f"{inst} longitude {lon} outside Jezero region"
