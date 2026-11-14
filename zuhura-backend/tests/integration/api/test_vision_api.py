"""
Tests for the image analysis (vision) API.
Validates:
1. Feature detection (impact craters, dunes, gullies, RSL, layered sediments).
2. Analytical crater morphometry (simple vs complex, Pike d/D ratios, ejecta classification).
3. Multi-spectral band ratios (CRISM Fe3+, smectite clays, olivine) and THEMIS thermal inertia.
4. Multi-temporal change detection (new impacts, slope streaks, ripple migration).
5. Sub-pixel image registration and projective homography matrix.
6. Super-resolution morphological detail enhancement.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from zuhura.api.main import app
from zuhura.vision.feature_detection import (
    profile_crater_morphology,
    detect_planetary_features,
)
from zuhura.vision.multispectral import (
    calculate_spectral_indices,
    calculate_thermal_inertia,
    run_multispectral_analysis,
)
from zuhura.vision.registration import (
    register_orbital_images,
    detect_temporal_surface_changes,
    apply_super_resolution_enhancement,
)


@pytest.mark.asyncio
async def test_detect_features_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/spatial/vision/detect-features",
            json={"latitude": 18.38, "longitude": 77.58, "radius_km": 50.0}
        )
        assert resp.status_code == 200
        features = resp.json()
        assert len(features) >= 2

        types = [f["feature_type"] for f in features]
        assert "impact_crater" in types
        assert "layered_sediments" in types or "aeolian_dunes_ripples" in types

        for f in features:
            assert f["confidence_score"] >= 0.85
            assert "bounding_box" in f
            assert f["bounding_box"]["width_m"] > 0
            assert f["epistemic_classification"] == "OBSERVED"


@pytest.mark.asyncio
async def test_crater_morphology_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Simple crater (3.0 km)
        resp_simple = await client.post(
            "/api/v1/spatial/vision/crater-profile",
            json={"latitude": 18.40, "longitude": 77.50, "diameter_km": 3.0}
        )
        assert resp_simple.status_code == 200
        simple = resp_simple.json()
        assert simple["crater_class"] == "SIMPLE"
        assert simple["central_peak_present"] is False
        assert simple["ejecta_blanket_type"] == "RADIAL_RAYED"
        assert 0.10 <= simple["depth_to_diameter_ratio"] <= 0.25

        # 2. Complex crater (47.5 km)
        resp_complex = await client.post(
            "/api/v1/spatial/vision/crater-profile",
            json={"latitude": 18.38, "longitude": 77.58, "diameter_km": 47.5}
        )
        assert resp_complex.status_code == 200
        complex_c = resp_complex.json()
        assert complex_c["crater_class"] == "COMPLEX"
        assert complex_c["central_peak_present"] is True
        assert complex_c["ejecta_blanket_type"] == "CONTINUOUS_RAMPART"
        assert complex_c["apparent_depth_m"] > 1000.0


@pytest.mark.asyncio
async def test_multispectral_analysis_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Jezero Delta Scarp (known smectite clay deposit)
        resp = await client.post(
            "/api/v1/spatial/vision/multispectral-analysis",
            json={"latitude": 18.42, "longitude": 77.48}
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "spectral_indices" in data
        indices = data["spectral_indices"]
        assert indices["dominant_mineralogy"] == "PHYLLOSILICATE_SMECTITE_CLAYS"
        assert indices["phyllosilicate_clay_index"] > 0.05
        assert indices["iron_oxide_index"] > 1.0

        assert "thermal_inertia" in data
        ti = data["thermal_inertia"]
        assert ti["derived_thermal_inertia_tiu"] > 200.0
        assert ti["estimated_grain_size_um"] > 50.0

        assert "false_color_rgb" in data
        assert "hex" in data["false_color_rgb"]


@pytest.mark.asyncio
async def test_change_detection_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/spatial/vision/change-detection",
            json={
                "latitude": 18.45,
                "longitude": 77.42,
                "epoch_1_date": "2021-01-01",
                "epoch_2_date": "2024-01-01"
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_changes_detected"] >= 3

        types = [c["change_type"] for c in data["changes"]]
        assert "NEW_IMPACT_CRATER" in types
        assert "SLOPE_STREAK" in types
        assert "DUNE_MIGRATION" in types

        for c in data["changes"]:
            assert c["confidence_score"] >= 0.90
            assert c["relative_albedo_delta_pct"] != 0.0


@pytest.mark.asyncio
async def test_image_registration_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/spatial/vision/image-registration",
            json={
                "reference_frame_id": "CTX_D14_032549_1985",
                "target_frame_id": "HiRISE_ESP_04299_1985"
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["matched_keypoints_count"] >= 200
        assert data["inlier_matches_count"] > 100
        assert data["inlier_ratio"] > 0.50
        assert data["subpixel_alignment_rmse_pixels"] < 0.50
        assert data["registration_quality"] in ("SUBPIXEL_EXCELLENT", "ACCEPTABLE")
        assert len(data["homography_matrix_3x3"]) == 3


@pytest.mark.asyncio
async def test_super_resolution_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/spatial/vision/super-resolution?original_resolution_m_per_px=6.0&enhancement_factor=2.0"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["enhanced_resolution_m_per_px"] == 3.0
        assert data["psnr_db"] > 30.0
        assert data["ssim_score"] > 0.90
        assert len(data["features_revealed"]) >= 3
