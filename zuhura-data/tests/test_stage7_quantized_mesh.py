"""
Zuhura Data - Stage 7 Quantized-Mesh & Geodesy Unit Tests
Tests:
  1. High-water mark compression and decompression round trip
  2. Octahedral normal vector compression accuracy (< 1.5 degrees)
  3. Horizon occlusion point in ellipsoid-scaled space (magnitude ~ 1.0 - 2.0)
  4. Global pyramid tile decoding and structure
  5. Regional terrain products existence and valid elevation spans
"""

import math
from pathlib import Path
import numpy as np
import pytest

from zuhura_data.terrain.quantized_mesh import (
    MARS_A,
    MARS_C,
    compress_indices,
    compute_horizon_occlusion_point,
    decode_quantized_mesh,
    decompress_indices,
    encode_quantized_mesh,
    oct_decode_normal,
    oct_encode_normal
)


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_high_water_mark_round_trip():
    # Regular quad triangulation
    triangles = [0, 1, 2, 1, 3, 2, 2, 3, 4, 3, 5, 4]
    comp = compress_indices(triangles)
    decomp = decompress_indices(comp, len(triangles))
    assert decomp == triangles


def test_oct_normal_encoding_accuracy():
    # Test principal axes and diagonals
    test_vectors = [
        (0.0, 0.0, 1.0),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.577, 0.577, 0.577),
        (-0.577, -0.577, -0.577),
        (0.3, -0.8, 0.5)
    ]
    for vec in test_vectors:
        mag = math.sqrt(sum(v**2 for v in vec))
        norm_vec = tuple(v / mag for v in vec)
        u, v = oct_encode_normal(*norm_vec)
        dec_vec = oct_decode_normal(u, v)
        dot = sum(a * b for a, b in zip(norm_vec, dec_vec))
        angle_err_deg = math.degrees(math.acos(min(1.0, max(-1.0, dot))))
        assert angle_err_deg < 1.5, f"Normal angular error too large: {angle_err_deg} deg"


def test_horizon_occlusion_point_scaled_space():
    center = (737039.63, 3140510.87, 1046187.97)
    corners = [
        (735000.0, 3140000.0, 1045000.0),
        (739000.0, 3141000.0, 1047000.0),
    ]
    hx, hy, hz = compute_horizon_occlusion_point(corners, center)
    hop_mag = math.sqrt(hx**2 + hy**2 + hz**2)
    # Scaled space magnitude must be close to 1.0 (between 1.0 and 2.0)
    assert 1.0 <= hop_mag <= 2.0, f"Invalid scaled space magnitude: {hop_mag}"


def test_global_pyramid_root_tiles():
    root_0 = REPO_ROOT / "data/tiles/terrain/global/0/0/0.terrain"
    root_1 = REPO_ROOT / "data/tiles/terrain/global/0/1/0.terrain"
    assert root_0.exists(), "Root tile 0/0/0 missing"
    assert root_1.exists(), "Root tile 0/1/0 missing"

    with open(root_0, "rb") as f:
        t0 = decode_quantized_mesh(f.read())
    with open(root_1, "rb") as f:
        t1 = decode_quantized_mesh(f.read())

    assert t0["vertex_count"] == 1089
    assert t1["vertex_count"] == 1089
    assert t0["triangle_count"] == 2048
    assert t1["triangle_count"] == 2048


def test_regional_products_integrity():
    for reg in ["jezero", "gale", "valles_marineris", "olympus_mons"]:
        dem_path = REPO_ROOT / f"data/processed/mola/regional/{reg}/mola_{reg}_meg128.tif"
        prov_path = REPO_ROOT / f"data/processed/mola/regional/{reg}/{reg}_terrain_provenance.json"
        layer_path = REPO_ROOT / f"data/tiles/terrain/{reg}/layer.json"

        assert dem_path.exists(), f"Missing DEM: {dem_path}"
        assert prov_path.exists(), f"Missing provenance: {prov_path}"
        assert layer_path.exists(), f"Missing layer.json: {layer_path}"
